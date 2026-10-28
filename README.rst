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

* License: GNU Lesser General Public License v3 or later (LGPL-3.0-or-later)
* Documentation: https://ecoledirecte-api.readthedocs.io.

Features
--------

* Asynchronous client for authenticating with the Ecole Directe API.
* Access to messages, homework, grades, school-life records, and timetables.
* Access to account services such as wallet balances, surveys, forms, and workspaces.
* Automatic re-authentication for supported operations after session errors.

Installation
------------

.. code:: console

   $ pip install ecoledirecte

Python compatibility
--------------------

This package requires Python 3.14 or later, below Python 4.0. This minimum is
intentional: the package is primarily used by Home Assistant and follows its
Python compatibility requirements.

Getting started
---------------

.. code:: python

    import asyncio

    from ecoledirecte_api.client import EDClient

    async def main():
        async with EDClient("username", "password", {}) as client:
            await client.login()
            homework = await client.get_homeworks("student_id")
            print(homework)

    if __name__ == "__main__":
        asyncio.run(main())

Replace the credentials and student ID with your own. If your account requires
QCM verification, provide the corresponding answers in the client's ``qcm_json``
argument.

Development - DevContainer (recommended)
----------------------------------------

If you use Visual Studio Code with Docker or GitHub CodeSpaces, you can leverage the available devcontainer. This will install all required dependencies and tools and has the right Python version available. Easy!


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _`Home Assistant Code`: https://github.com/hacf-fr/hass-ecoledirecte
