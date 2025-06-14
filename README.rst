=================
Ecole Directe API
=================
|PyPI| |Python Version| |License|

.. |PyPI| image:: https://img.shields.io/pypi/v/ecoledirecte.svg
   :target: https://pypi.org/project/ecoledirecte/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/ecoledirecte
   :target: https://pypi.org/project/ecoledirecte
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/ecoledirecte
   :target: https://opensource.org/licenses/lgpl-3-0
   :alt: License

A fully async and easy to use API client for the Ecole Directe API.
This package is mainly used by Home Assistant, to offer the Ecole Directe integration. If you want to use this package in your own project, you can look at the `Home Assistant Code`_ for more examples.

* Free software: GNU General Public License v3
* Documentation: https://ecoledirecte-api.readthedocs.io.

Features
--------

* TODO

Installation
------------

.. code:: console

   $ pip install ecoledirecte

Getting started
---------------

.. code:: python
        
    import asyncio
    import json
    import logging
    from pathlib import Path
    from ecoledirecte_api.client import EDClient
    from ecoledirecte_api.exceptions import BaseEcoleDirecteException
    
    logger = logging.getLogger(__name__)
    
    def save_question(qcm_json):
        """Save question to file."""
        with Path("qcm.json").open(
            "w",
            encoding="utf-8",
        ) as fp:
            json.dump(qcm_json, fp, indent=4, ensure_ascii=False)
        logger.info("Saved question to file", qcm_json)
    
    
    async def main():
        logging.basicConfig(filename="myapp.log", level=logging.DEBUG)
        logger.info("Started")
        try:
            qcm_json = {}
            with Path("qcm.json").open(
                "r",
                encoding="utf-8",
            ) as fp:
                qcm_json = json.load(fp)
    
                async with EDClient(
                    "user", "password", qcm_json
                ) as client:
                    client.on_new_question(save_question)
                    l = await client.login()
                    logger.info(f"l= {l}")
                    logger.info(f"Logged in as {client.username}")
                    logger.info("Finished")
                    await client.close()
        except BaseEcoleDirecteException as e:
            logger.exception(e.message)
            return
        except Exception as e:
            logger.exception(e)
            return
    
    if __name__ == "__main__":
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())

Development - DevContainer (recommended)
----------------------------------------

If you use Visual Studio Code with Docker or GitHub CodeSpaces, you can leverage the available devcontainer. This will install all required dependencies and tools and has the right Python version available. Easy!


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`Home Assistant Code`: https://github.com/hacf-fr/hass-ecoledirecte

