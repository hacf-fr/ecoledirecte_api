"""Python wrapper for the Ecole Directe API."""

from __future__ import annotations

import base64
import logging
from collections.abc import Mapping
from json import JSONDecodeError
from types import TracebackType
from typing import Any
import backoff
from aiohttp import (
    ClientConnectorError,
    ClientResponse,
    ClientSession,
    ServerDisconnectedError,
)

from .const import APIURL, APIVERSION, ED_MFA_REQUIRED, ED_NODATA, ED_OK
from .exceptions import (
    EcoleDirecteException,
    GTKException,
    LoginException,
    MFARequiredException,
    NotAuthenticatedException,
    QCMException,
    ServiceUnavailableException,
)

LOGGER = logging.getLogger(__name__)


async def relogin(invocation: Mapping[str, Any]) -> None:
    LOGGER.debug("Re-authenticating...")
    await invocation["args"][0].freshlogin()


class EDClient:
    """Interface class for the Ecole Directe API"""

    username: str
    password: str
    _session: ClientSession
    token: str
    callbacks = None

    def __init__(
        self,
        username: str,
        password: str,
        qcm_json: dict,
        token: str | None = None,
        cookie_jar: Any = None,
        server_endpoint: str = APIURL,
        api_version: str = APIVERSION,
    ) -> None:
        """
        Constructor

        :param username: the username
        :param password: the password
        :param qcm_json: the QCM json
        :param server_endpoint: the server endpoint (default: APIURL)
        :param api_version: the API version (default: APIVERSION)
        """

        self.username = username
        self.password = password
        self.qcm_json = qcm_json
        self.server_endpoint = server_endpoint
        self.api_version = api_version
        self._session: ClientSession = None
        self.token: str = token
        self._cookie_jar: Any = cookie_jar

    async def __aenter__(self) -> EDClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session."""
        if self._session is not None:
            await self._session.close()
            self._session = None

    def __get_new_client__(self) -> None:
        """Create a new aiohttp client session."""

        LOGGER.debug("Creating new ClientSession with cookies: [%s]", self._cookie_jar)

        self._session = ClientSession(
            headers={
                "accept": "application/json, text/plain, */*",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "fr-FR,fr;q=0.9",
                "connection": "keep-alive",
                "content-type": "application/x-www-form-urlencoded",
                "dnt": "1",
                "origin": "https://www.ecoledirecte.com",
                "priority": "1",
                "referer": "https://www.ecoledirecte.com/",
                "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            },
            cookie_jar=self._cookie_jar,
            # MODIFIÉ: Passe de True à False pour éviter la lecture bloquante du fichier .netrc
            trust_env=False,
        )

        if self.token is not None:
            self._session.headers.update({"x-token": self.token})

    async def __get_gtk__(self) -> None:
        """Get the gtk value from the server."""
        # first call to get a cookie
        if "x-gtk" in self._session.headers:
            self._session.headers.pop("x-gtk")
        resp = await self._session.get(
            f"{self.server_endpoint}/login.awp",
            params={"v": self.api_version, "gtk": 1},
            data=None,
            timeout=120,
        )
        if "GTK" in resp.cookies:
            self._session.headers.update({"x-gtk": resp.cookies["GTK"].value})
            return
        raise GTKException("Unable to get GTK value from server.")

    async def __get_token__(self, payload: str) -> Any:
        """Get the token value from the server."""
        LOGGER.debug(
            f"headers request: [{self._session.headers}] - payload: [{payload}]"
        )
        response = await self._session.post(
            f"{self.server_endpoint}/login.awp",
            params={"v": self.api_version},
            data=payload,
            timeout=120,
        )
        await self.check_response(
            response=response,
            path=f"{self.server_endpoint}/login.awp",
            payload=payload,
            bypassMFA=True,
        )
        json = await response.json(content_type=None)
        LOGGER.debug(f"headers response: {response.headers}")
        LOGGER.debug(f"json response: {json}")

        self.token = response.headers["x-token"]
        self._session.headers.update({"x-token": self.token})

        if "x-gtk" in self._session.headers:
            self._session.headers.pop("x-gtk")

        self._cookie_jar = self._session.cookie_jar
        return json

    async def __get_qcm_connexion__(self) -> dict:
        """Obtenir le QCM donné lors d'une connexion à partir d'un nouvel appareil."""
        response = await self._session.post(
            url=f"{self.server_endpoint}/connexion/doubleauth.awp",
            params={"verbe": "get", "v": self.api_version},
            data="data={}",
            timeout=120,
        )
        try:
            json_resp = await response.json(content_type=None)
            LOGGER.debug(f"get_qcm_connexion={json_resp}]")
        except Exception as ex:
            msg = f"Error with URL:[{f'{self.server_endpoint}/connexion/doubleauth.awp'}]: {response.content}"
            raise QCMException(msg) from ex

        if json_resp["code"] != ED_OK:
            raise QCMException(json_resp)

        if "data" in json_resp:
            self.token = response.headers["x-token"]
            self._session.headers.update({"x-token": self.token})
            return json_resp["data"]

        raise QCMException(json_resp)

    async def __post_qcm_connexion__(self, proposition: str) -> dict:
        """Renvoyer la réponse du QCM donné."""
        response = await self._session.post(
            url=f"{self.server_endpoint}/connexion/doubleauth.awp",
            params={"verbe": "post", "v": self.api_version},
            data=f'data={{"choix": "{proposition}"}}',
            timeout=120,
        )
        json_resp = await response.json(content_type=None)

        if "data" in json_resp:
            self.token = response.headers["x-token"]
            self._session.headers.update({"x-token": self.token})
            return json_resp["data"]
        raise QCMException(json_resp)

    def on_new_question(self, callback):
        if self.callbacks is None:
            self.callbacks = {}
            self.callbacks["new_question"] = [callback]
        else:
            self.callbacks["new_question"].append(callback)

    async def freshlogin(self) -> None:
        LOGGER.debug("freshlogin...")
        await self.close()
        self._cookie_jar = None
        self.token = None
        await self.login()

    async def login(
        self,
    ) -> Any:
        """Authenticate and create an API session allowing access to the other operations."""
        if self._session is not None:
            await self._session.close()
        self.__get_new_client__()

        if self._cookie_jar is not None:
            return

        await self.__get_gtk__()
        payload = (
            'data={"identifiant":"'
            + self.encodeString(self.username)
            + '", "motdepasse":"'
            + self.encodeString(self.password)
            + '", "isRelogin": false}'
        )
        first_token = await self.__get_token__(payload)

        # Si connexion initiale
        if first_token["code"] == ED_MFA_REQUIRED:
            try_login = 2

            while try_login > 0:
                # Obtenir le qcm de vérification et les propositions de réponse
                qcm = await self.__get_qcm_connexion__()
                question = base64.b64decode(qcm["question"]).decode("utf-8")

                if question in self.qcm_json:
                    if len(self.qcm_json[question]) > 1:
                        try_login -= 1
                        continue
                    response = base64.b64encode(
                        bytes(self.qcm_json[question][0], "utf-8")
                    ).decode("ascii")
                    cn_et_cv = await self.__post_qcm_connexion__(
                        str(response),
                    )
                    # Si le quiz a été raté
                    if not cn_et_cv:
                        continue
                    cn = cn_et_cv["cn"]
                    cv = cn_et_cv["cv"]
                    break
                rep = []
                propositions = qcm["propositions"]
                for proposition in propositions:
                    rep.append(base64.b64decode(proposition).decode("utf-8"))

                self.qcm_json[question] = rep
                if self.callbacks is not None and "new_question" in self.callbacks:
                    LOGGER.info(f"callback new_question : [{question}]")
                    for callback in self.callbacks["new_question"]:
                        # wait for event to be handled
                        await callback(self.qcm_json)

                try_login -= 1

            if try_login == 0:
                msg = "Vérifiez le qcm de connexion, le nombre d'essais est épuisé."
                raise QCMException(msg)

            await self.__get_gtk__()

            # Renvoyer une requête de connexion avec la double-authentification réussie
            payload = (
                'data={"identifiant":"'
                + self.encodeString(self.username)
                + '", "motdepasse":"'
                + self.encodeString(self.password)
                + '", "isRelogin": false, "cn":"'
                + cn
                + '", "cv":"'
                + cv
                + '", "uuid": "", "fa": [{"cn": "'
                + cn
                + '", "cv": "'
                + cv
                + '"}]}'
            )
            return await self.__get_token__(payload)

    async def __get(self, path: str) -> Any:
        """Make a GET request to the Ecole Directe API"""
        if self._session is None:
            await self.login()

        response = await self._session.get(
            f"{self.server_endpoint}{path}",
        )
        await self.check_response(response=response, path=path)
        return await response.json(content_type=None)

    async def __post(
        self, path: str, params: dict | None = None, payload: Any | None = None
    ) -> Any:
        """Make a POST request to the Ecole Directe API"""
        if self._session is None:
            await self.login()

        response = await self._session.post(
            url=f"{self.server_endpoint}{path}",
            params=params,
            data=payload,
        )
        await self.check_response(response, path, params, payload)
        return await response.json(content_type=None)

    @staticmethod
    async def check_response(
        response: ClientResponse,
        path: str,
        params: dict | None = None,
        payload: Any | None = None,
        bypassMFA: bool = False,
    ) -> None:
        """Check the response returned by the Ecole Directe API"""
        try:
            result = await response.json(content_type=None)
        except JSONDecodeError as error:
            result = await response.text()

            if response.status >= 500 and response.status < 600:
                raise ServiceUnavailableException(result) from error

            raise EcoleDirecteException(
                path=path,
                params=params,
                payload=payload,
                status=response.status,
                message=result,
            ) from error

        if code := result.get("code"):
            if code == ED_OK:
                return

            if code == ED_NODATA:
                return

            if code == ED_MFA_REQUIRED and bypassMFA is True:
                return

            if code == ED_MFA_REQUIRED:
                raise MFARequiredException(
                    path=path,
                    params=params,
                    payload=payload,
                    message="MFARequiredException",
                )

            if code == 505:
                raise LoginException(
                    path=path,
                    params=params,
                    payload=payload,
                    message="LoginException",
                )

            if code == 517:
                raise EcoleDirecteException(
                    path=path,
                    params=params,
                    payload=payload,
                    message="La version de l'API utilisée est invalide",
                )

            if code == 520:
                raise LoginException(
                    path=path,
                    params=params,
                    payload=payload,
                    message="Le token est invalide",
                )

            if code == 525:
                raise LoginException(
                    path=path,
                    params=params,
                    payload=payload,
                    message="Le token est expiré",
                )

        # Undefined Ecole Directe exception
        raise EcoleDirecteException(
            path=path, params=params, payload=payload, message=result
        )

    def encodeString(self, string):
        return (
            string.replace("%", "%25")
            .replace("&", "%26")
            .replace("+", "%2B")
            .replace("+", "%2B")
            .replace("\\", "\\\\\\")
            .replace("\\\\", "\\\\\\\\")
        )

    def encodeBody(self, dictionnary, isRecursive=False):
        body = ""
        for key in dictionnary:
            if isRecursive:
                body += '"' + key + '":'
            else:
                body += key + "="

            if type(dictionnary[key]) is dict:
                body += "{" + self.encodeBody(dictionnary[key], True) + "}"
            else:
                body += '"' + str(dictionnary[key]) + '"'
            body += ","

        return body[:-1]

    async def get_cookies(self) -> Any:
        """Get cookies."""
        LOGGER.debug("get_cookies")
        if self._session is None:
            return None
        return await self._session.cookie_jar

    @backoff.on_exception(
        backoff.expo,
        (NotAuthenticatedException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_messages(
        self, family_id: str | None, eleve_id: str | None, annee_scolaire: str
    ) -> dict:
        """Get messages from Ecole Directe."""
        LOGGER.debug(
            "get_messages: family_id=%s, eleve_id=%s, annee_scolaire=%s",
            family_id,
            eleve_id,
            annee_scolaire,
        )
        payload = 'data={"anneeMessages":"' + annee_scolaire + '"}'
        if eleve_id is None:
            path = f"/familles/{family_id}/messages.awp"
        else:
            path = f"/eleves/{eleve_id}/messages.awp"

        return await self.__post(
            path=path,
            params={
                "force": "false",
                "typeRecuperation": "received",
                "idClasseur": "0",
                "orderBy": "date",
                "order": "desc",
                "query": "",
                "onlyRead": "",
                "page": "0",
                "itemsPerPage": "100",
                "getAll": "0",
                "verbe": "get",
                "v": APIVERSION,
            },
            payload=payload,
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_homeworks_by_date(self, eleve_id: str, date: str) -> dict:
        """Get homeworks by date."""
        LOGGER.debug(
            "get_homeworks_by_date: eleve_id=%s, date=%s",
            eleve_id,
            date,
        )
        return await self.__post(
            path=f"/Eleves/{eleve_id}/cahierdetexte/{date}.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_homeworks(self, eleve_id: str) -> dict:
        """Get homeworks."""
        LOGGER.debug("get_homeworks: eleve_id=%s", eleve_id)
        return await self.__post(
            path=f"/Eleves/{eleve_id}/cahierdetexte.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def post_homework(
        self, eleve_id: str, devoir_id: int, effectue: bool
    ) -> dict:
        """Post homework."""
        LOGGER.debug(
            "post_homework: eleve_id=%s, devoir_id=%s, effectue=%s",
            eleve_id,
            devoir_id,
            effectue,
        )
        if effectue:
            payload = (
                'data={"idDevoirsEffectues": ['
                + str(devoir_id)
                + '],"idDevoirsNonEffectues": []}'
            )
        else:
            payload = (
                'data={"idDevoirsEffectues": [],"idDevoirsNonEffectues": ['
                + str(devoir_id)
                + "]}"
            )
        return await self.__post(
            path=f"/Eleves/{eleve_id}/cahierdetexte.awp",
            params={"verbe": "put", "v": APIVERSION},
            payload=payload,
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_grades_evaluations(
        self,
        eleve_id: str,
        annee_scolaire: str,
    ) -> dict:
        """Get grades."""
        LOGGER.debug(
            "get_grades_evaluations: eleve_id=%s, annee_scolaire=%s",
            eleve_id,
            annee_scolaire,
        )
        return await self.__post(
            path=f"/eleves/{eleve_id}/notes.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload=f"data={{'anneeScolaire': '{annee_scolaire}'}}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_vie_scolaire(self, eleve_id: str) -> dict:
        """Get vie scolaire (absences, retards, etc.)."""
        LOGGER.debug("get_vie_scolaire: eleve_id=%s", eleve_id)
        return await self.__post(
            path=f"/eleves/{eleve_id}/viescolaire.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_lessons(self, eleve_id: str, date_debut: str, date_fin: str) -> dict:
        """Get lessons."""
        LOGGER.debug(
            "get_lessons: eleve_id=%s, date_debut=%s, date_fin=%s",
            eleve_id,
            date_debut,
            date_fin,
        )
        return await self.__post(
            path=f"/E/{eleve_id}/emploidutemps.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload=f"data={{'dateDebut': '{date_debut}','dateFin': '{
                date_fin
            }','avecTrous': false}}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_all_wallet_balances(self) -> dict:
        """Get all wallet balances for the account."""
        LOGGER.debug("get_all_wallet_balances")
        return await self.__post(
            path="/comptes/sansdetails.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_sondages(self) -> dict:
        """Get sondages."""
        LOGGER.debug("get_sondages")
        return await self.__post(
            path=f"/rdt/sondages.awp?v={APIVERSION}",
            params={"v": APIVERSION},
            payload="data={}",
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_formulaires(self, account_type: str, id_entity: str) -> dict:
        """Get formulaires."""
        LOGGER.debug(
            "get_formulaires: account_type=%s, id_entity=%s", account_type, id_entity
        )
        payload = (
            'data={"typeEntity": "'
            + str(account_type)
            + '","idEntity":'
            + str(id_entity)
            + "}"
        )
        return await self.__post(
            path="/edforms.awp",
            params={"verbe": "list", "v": APIVERSION},
            payload=payload,
        )

    @backoff.on_exception(
        backoff.expo,
        (LoginException, ServerDisconnectedError, ClientConnectorError),
        max_tries=2,
        on_backoff=relogin,
    )
    async def get_classe(self, classe_id: str) -> None:
        """Get classe."""
        LOGGER.debug("get_classe: classe_id=%s", classe_id)
        json_resp = self.__post(
            path=f"/Classes/{classe_id}/viedelaclasse.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
        )
        LOGGER.debug("get_classeV1: [%s]", json_resp)

        json_resp = self.__post(
            path=f"/R/{classe_id}/viedelaclasse.awp",
            params={"verbe": "get", "v": APIVERSION},
            payload="data={}",
        )
        LOGGER.debug("get_classeV2: [%s]", json_resp)
