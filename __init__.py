"""Unit test package for ecoledirecte_api."""

from src.ecoledirecte_api.client import EDClient
from src.ecoledirecte_api.exceptions import BaseEcoleDirecteException
import asyncio
import json
import logging
from pathlib import Path
import sys

sys.path.insert(1, "/src/ecoledirecte_api")


# caution: path[0] is reserved for script path (or '' in REPL)

logger = logging.getLogger(__name__)


async def save_question(qcm_json):
    """Save question to file."""
    with Path("qcm_gaspar.json").open(
        "w",
        encoding="utf-8",
    ) as fp:
        json.dump(qcm_json, fp, indent=4, ensure_ascii=False)
    logger.info("Saved question to file", qcm_json)


async def main():
    logging.basicConfig(filename="myapp.log", level=logging.DEBUG)
    logger.info("Started")
    try:

        # identifiant = "Monestier.luca13"
        # password = "Titine@81800"
        # qcm_path = "qcm_luca.json"

        identifiant = "FamilleGaspar"
        password = "n3d~()*!.'#C-drsd+D7\\A1*NkKC%TXq"
        qcm_path = "qcm_gaspar.json"

        qcm_json = {}
        with Path(qcm_path).open(
            "r",
            encoding="utf-8",
        ) as fp:
            qcm_json = json.load(fp)
            async with EDClient(
                identifiant,
                password,
                qcm_json,
            ) as client:
                client.on_new_question(save_question)
                l = await client.login()
                logger.info(f"l= {l}")
                logger.info(f"Logged in as {client.username}")

            async with EDClient(
                identifiant,
                password,
                qcm_json,
            ) as client:
                client.on_new_question(save_question)
                l = await client.login()
                # logger.info(f"l= {l}")
                # logger.info(f"Logged in as {client.username}")
                # logger.info(f"Data: {client.data}")

                # await client.close()
                # vs_elena = await client.get_vie_scolaire("2157")  # elena
                # logger.info(f"Re Elena data: {vs_elena}")

                # client._session.headers.pop("x-token", None)

                wallets = await client.get_all_wallet_balances()
                logger.info(f"Wallets: {wallets}")

                # vs_elena = await client.get_vie_scolaire("2157")  # elena
                # logger.info(f"Elena data: {vs_elena}")
                vs_noeline = await client.get_vie_scolaire("2113")  # noeline
                logger.info(f"Noeline data: {vs_noeline}")

                forms = await client.get_formulaires("2026-2027", "E", "2113")
                logger.info(f"Forms: {forms}")

                # FamilleGaspar
                # espaces = await client.get_all_espaces_travail("3745", 1)
                # logger.info(f"Workspaces: {espaces}")

                # espace859 = await client.get_espace_travail("859", "3745", 1)
                # logger.info(f"Workspace 859: {espace859}")

                # postits859 = await client.get_postits("859")
                # logger.info(f"Post-its 859: {postits859}")

                # activites859 = await client.get_activites_espace_travail("859", 3745, 1)
                # logger.info(f"Activities 859: {activites859}")

                # detailsactivites859 = await client.get_details_cloudactivites_espace_travail("859", 406, "P", "202609170429")
                # logger.info(f"Activities 859: {detailsactivites859}")

                # menus = await client.get_menus("2113")
                # logger.info(f"Menus: {menus}")

                # file = await client.download_file(36, "FICHIER_MENU_RESTAURATION")
                # file_content = await file.read() if hasattr(file, "read") else file
                # ext = ".pdf"
                # if file_content.startswith(b"%PDF"):
                #     ext = ".pdf"
                # elif file_content.startswith(b"\x89PNG"):
                #     ext = ".png"
                # elif file_content.startswith(b"\xff\xd8\xff"):
                #     ext = ".jpg"

                # output_path = Path(__file__).parent / f"menu_36{ext}"
                # output_path.write_bytes(file_content)
                # logger.info(f"File written to {output_path}")

                # sw_acc = await client.switch_account("2901416")
                # logger.info(f"Switched account: {sw_acc}")

                # h = await client.post_homework("2091", 1053, False)
                # logger.info(h)
                # h = await client.get_homeworks("2091")
                # logger.info(h)
                # h12 = await client.get_homeworks_by_date("2091", "2023-06-12")
                # logger.info(h12)
                logger.info("Finished")
                await client.close()
    except BaseEcoleDirecteException as e:
        logger.exception(e.message)
        return
    except Exception as e:
        logger.exception(e)
        return


if __name__ == "__main__":
    asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())
