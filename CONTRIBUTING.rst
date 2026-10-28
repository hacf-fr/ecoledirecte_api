.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/hacf-fr/ecoledirecte_api/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

Ecole Directe API could always use more documentation, whether as part of the
official Ecole Directe API docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/hacf-fr/ecoledirecte_api/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `ecoledirecte_api` for local development.

1. Fork the `ecoledirecte_api` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/ecoledirecte_api.git

3. Install Poetry, then install the project and its development dependencies::

    $ cd ecoledirecte_api/
    $ poetry install

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. The project currently supports Python 3.14 and later versions below 4.0.
   Run the configured linter, type checker, and tests before submitting::

    $ poetry run ruff check src tests
    $ poetry run mypy
    $ poetry run pytest

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. Ensure the changes are compatible with the supported Python versions
   (currently Python 3.14 or later, below 4.0) and that the checks above pass.

Tips
----

To run a specific test file::

    $ poetry run pytest tests/test_ecoledirecte_api.py


Code of Conduct
---------------

Please note that this project is released with a `Contributor Code of Conduct`_.
By participating in this project you agree to abide by its terms.

.. _`Contributor Code of Conduct`: CODE_OF_CONDUCT.rst
