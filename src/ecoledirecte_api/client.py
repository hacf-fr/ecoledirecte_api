"""Python wrapper for the Ecole Directe API."""

from __future__ import annotations

import base64
import logging
import urllib.parse
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

from .const import APIURL, APIVERSION, ED_MFA_REQUIRED, ED_OK
from .exceptions import (
    EcoleDirecteException,
    GTKException,
    LoginException,
    MFARequiredException,
    QCMException,
    ServiceUnavailableException,
)
from .models import EDEleve

logger = logging.getLogger(__name__)

async def relogin(invocation: Mapping[str, Any]) -> None:
    await invocation["args"][0].login()


# pylint: disable=too-many-instance-attributes, too-many-branches


class EDClient:
    """Interface class for the Ecole Directe API"""

    username: str
    password: str
    session: ClientSession

    def __init__(
        self,
        username: str,
        password: str,
        qcm_json: Any,
        server_endpoint: str = APIURL,
        api_version: str = APIVERSION,
        session: ClientSession | None = None,
    ) -> None:
        """
        Constructor

        :param username: the username
        :param password: the password
        :param session: optional ClientSession
        """

        self.username = username
        self.password = password
        self.qcm_json = qcm_json
        self.server_endpoint = server_endpoint
        self.api_version = api_version
        self.session = session if session else self.__get_new_client__()

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
        await self.session.close()

    def __get_new_client__(self) -> ClientSession:
        """Create a new aiohttp client session."""
        return ClientSession(
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
            }
        )

    async def __get_gtk__(self) -> None:
        """Get the gtk value from the server."""
        # first call to get a cookie
        if "x-gtk" in self.session.headers:
            self.session.headers.pop("x-gtk")
        resp = await self.session.get(
            f"{self.server_endpoint}/login.awp",
            params={"v": self.api_version, "gtk": 1},
            data=None,
            timeout=120,
        )
        if "GTK" in resp.cookies:
            self.session.headers.update({"x-gtk": resp.cookies["GTK"].value})
            return
        raise GTKException("Unable to get GTK value from server.")

    async def __get_token__(self, payload: str) -> Any:
        """Get the token value from the server."""
        # Post credentials to get a token
        # async with self.session.post(
        #     f"{self.server_endpoint}/login.awp",
        #     params={"v": self.api_version},
        #     data=payload,
        #     timeout=120) as response:
        #     self.token = response.headers["x-token"]

        logger.debug(f"payload: {payload}")
        logger.debug(f"headers: {self.session.headers}")

        response = await self.session.post(
            f"{self.server_endpoint}/login.awp",
            params={"v": self.api_version},
            data=payload,
            timeout=120,
        )
        json = await response.json()
        logger.debug(f"response: {json}")

        self.token = response.headers["x-token"]
        self.session.headers.update({"x-token": self.token})
        return json 

    async def __get_qcm_connexion__(self) -> dict:
        """Obtenir le QCM donné lors d'une connexion à partir d'un nouvel appareil."""
        response = await self.session.post(
            url=f"{self.server_endpoint}/connexion/doubleauth.awp",
            params={"verbe": "get", "v": self.api_version},
            data="data={}",
            timeout=120,
        )
        try:
            json_resp = await response.json()
        except Exception as ex:
            msg = f"Error with URL:[{f'{self.server_endpoint}/connexion/doubleauth.awp'}]: {response.content}"
            raise QCMException(msg) from ex

        if json_resp["code"] != ED_OK:
            raise QCMException(json_resp)

        if "data" in json_resp:
            self.token = response.headers["x-token"]
            self.session.headers.update({"x-token": self.token})
            return json_resp["data"]

        raise QCMException(json_resp)

    async def __post_qcm_connexion__(self, proposition: str) -> dict:
        """Renvoyer la réponse du QCM donné."""
        response = await self.session.post(
            url=f"{self.server_endpoint}/connexion/doubleauth.awp",
            params={"verbe": "post", "v": self.api_version},
            data=f'data={{"choix": "{proposition}"}}',
            timeout=120,
        )
        json_resp = await response.json()

        if "data" in json_resp:
            self.token = response.headers["x-token"]
            self.session.headers.update({"x-token": self.token})
            return json_resp["data"]
        raise QCMException(json_resp)

    async def login(
        self,
    ) -> bool:
        """Authenticate and create an API session allowing access to the other operations."""
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
            try_login = 5

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

                # trigger event self.qcm_json
                # event_data = {
                #     "device_id": "ED - " + self.username,
                #     "type": "new_qcm",
                #     "question": question,
                # }
                # self.hass.bus.fire(EVENT_TYPE, event_data)
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
            login = await self.__get_token__(payload)

            self.data = login["data"]
            self.id = self.data["accounts"][0]["id"]
            self.identifiant = self.data["accounts"][0]["identifiant"]
            self.id_login = self.data["accounts"][0]["idLogin"]
            self.account_type = self.data["accounts"][0]["typeCompte"]
            self.modules = []
            for module in self.data["accounts"][0]["modules"]:
                if module["enable"]:
                    self.modules.append(module["code"])
            self.eleves = []
            if self.account_type == "E":
                self.eleves.append(
                    EDEleve(
                        None,
                        self.data["accounts"][0]["nomEtablissement"],
                        self.id,
                        self.data["accounts"][0]["prenom"],
                        self.data["accounts"][0]["nom"],
                        self.data["accounts"][0]["profile"]["classe"]["id"],
                        self.data["accounts"][0]["profile"]["classe"]["libelle"],
                        self.modules,
                    )
                )
            elif "eleves" in self.data["accounts"][0]["profile"]:
                for eleve in self.data["accounts"][0]["profile"]["eleves"]:
                    self.eleves.append(
                        EDEleve(
                            eleve,
                            self.data["accounts"][0]["nomEtablissement"],
                        )
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

    # @backoff.on_exception(
    #     backoff.expo,
    #     (NotAuthenticatedException, ServerDisconnectedError, ClientConnectorError),
    #     max_tries=2,
    #     on_backoff=relogin,
    # )
    # async def get_device_definition(self, deviceurl: str) -> Any | None:
    #     """
    #     Retrieve a particular setup device definition
    #     """
    #     response: dict = await self.__get(
    #         f"setup/devices/{urllib.parse.quote_plus(deviceurl)}"
    #     )

    #     return response.get("definition")

    async def __get(self, path: str) -> Any:
        """Make a GET request to the Ecole Directe API"""
        async with self.session.get(
            f"{self.server_endpoint}{path}",
        ) as response:
            await self.check_response(response)
            return await response.json()

    async def __post(
        self, path: str, payload: Any | None = None, data: Any | None = None
    ) -> Any:
        """Make a POST request to the Ecole Directe API"""

        async with self.session.post(
            f"{self.server.endpoint}{path}",
            data=data,
            json=payload,
        ) as response:
            await self.check_response(response)
            return await response.json()

    @staticmethod
    async def check_response(response: ClientResponse) -> None:
        """Check the response returned by the Ecole Directe API"""
        try:
            result = await response.json(content_type=None)
        except JSONDecodeError as error:
            result = await response.text()

            if response.status >= 500 and response.status < 600:
                raise ServiceUnavailableException(result) from error

            raise EcoleDirecteException(
                f"Unknown error while requesting {response.url}. {response.status} - {result}"
            ) from error

        if code := result.get("code"):
            if code == ED_OK:
                return

            if code == ED_MFA_REQUIRED:
                raise MFARequiredException()

        # Undefined Ecole Directe exception
        raise EcoleDirecteException(result)
