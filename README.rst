datadir-mgr plugin for pytest
=============================

The ``datadir-mgr`` plugin for pytest_ provides the ``datadir_mgr`` fixture which
allow test functions to easily download data files and cache generated data files
in data directories in a manner that allows for overlaying of results. ``datadir-mgr``
is pathlib-based, so complete paths to data files are handled,
not just filenames.



The ``datadir_mgr`` behaves like a limited dictionary, with ``datadir_mgr[item]`` returning a path with the
most specific scope (out of ``global, module, [class], [function]`` that matches the string or path specified
by ``item``.  In addition to serving data files already stored in the data directory, the fixture provides
five methods useful for adding to the test data stored in the repository:

- The ``download`` method allows downloading data files into data directories, with
  option MD5 checksum checks, un-gzipping, and a progressbar.
- The ``savepath`` fixture lets an arbitrary path relative to the current working
  directory to be saved at a particular scope in the data directories.
- The ``add_scope`` method lets one add directories from scopes different from
  the present request to be added to the search path.  This lets the results
  of previous cached steps to be used in scopes other than global.
- The ``in_tmp_dir`` method creates a context in a temporary directory with
  a list of request file paths copied in.  Optionally, all output file paths
  can be saved at a particular scope at cleanup with an optional exclusion
  filter pattern (e.g., for excluding log files).  Note that files in directories
  that begin with ``test_`` or end with ``_test`` could be confused with
  scope directories and cannnot be saved.  If ``progressbar`` is set to "True",
  then the progress of file copying will be shown, which is helpful in some long-running
  pytest jobs, e.g. on Travis.
- The ``paths_from_scope`` returns a list of all paths to files from a specified scope.


Prerequisites
-------------
Python 3.6 or greater is required.
This package is tested under Linux and MacOS using Python 3.8.

Installation for Users
----------------------
Install via pip ::

     pip install pytest-datadir-mgr

For Developers
--------------
If you plan to develop ``datadir_mgr``, you'll need to install
the `poetry <https://python-poetry.org>`_ dependency manager.
If you haven't previously installed ``poetry``, execute the command: ::

    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

Next, get the master branch from GitHub ::

	git clone https://github.com/legumeinfo/pytest-datadir-mgr.git

Change to the ``datadir-mgr/`` directory and install with poetry: ::

	poetry install -v

Test ``datadir-mgr`` with ``poetry``: ::

    poetry run pytest -s

Project Status
--------------
+-------------------+-------------+
| Latest Release    | |pypi|      |
+-------------------+-------------+
| Activity          | |downloads| |
+-------------------+-------------+
| License           | |license|   |
+-------------------+-------------+
| Travis Build      | |travis|    |
+-------------------+-------------+
| Coverage          | |coverage|  |
+-------------------+-------------+
| Code Grade        | |codacy|    |
+-------------------+-------------+
| Issues            | |issues|    |
+-------------------+-------------+

.. _pytest: http://pytest.org/

.. |pypi| image:: https://img.shields.io/pypi/v/pytest-datadir-mgr.svg
    :target: https://pypi.python.org/pypi/pytest-datadir-mgr
    :alt: Python package

.. |repo| image:: https://img.shields.io/github/commits-since/legumeinfo/pytest-datadir-mgr/0.1.0.svg
    :target: https://github.com/legumeinfo/pytest-datadir-mgr
    :alt: GitHub repository

.. |license| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
    :target: https://github.com/legumeinfo/pytest-datadir-mgr/blob/master/LICENSE.txt
    :alt: License terms

.. |travis| image:: https://img.shields.io/travis/legumeinfo/pytest-datadir-mgr.svg
    :target:  https://travis-ci.org/legumeinfo/pytest-datadir-mgr
    :alt: Travis CI

.. |codacy| image:: https://api.codacy.com/project/badge/Grade/4580a0a576204fa688cbb75575a1c867
    :target: https://www.codacy.com/gh/legumeinfo/pytest-datadir-mgr?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=legumeinfo/pytest-datadir-mgr&amp;utm_campaign=Badge_Grade
    :alt: Codacy.io grade

.. |coverage| image:: https://codecov.io/gh/legumeinfo/pytest-datadir-mgr/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/legumeinfo/pytest-datadir-mgr
    :alt: Codecov.io test coverage

.. |issues| image:: https://img.shields.io/github/issues/legumeinfo/pytest-datadir-mgr.svg
    :target:  https://github.com/legumeinfo/pytest-datadir-mgr/issues
    :alt: Issues reported

.. |downloads| image:: https://pepy.tech/badge/pytest_datadir_mgr
     :target: https://pepy.tech/project/pytest_datadir_mgr
     :alt: Download stats
