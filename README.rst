=============================
Cell Maps Pipeline Utilities
=============================


.. image:: https://img.shields.io/pypi/v/cellmaps_utils.svg
        :target: https://pypi.python.org/pypi/cellmaps_utils

.. image:: https://img.shields.io/travis/idekerlab/cellmaps_utils.svg
        :target: https://travis-ci.com/idekerlab/cellmaps_utils

.. image:: https://readthedocs.org/projects/cellmaps-utils/badge/?version=latest
        :target: https://cellmaps-utils.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Contains utilities needed by various tools in the cell maps toolkit. 


* Free software: MIT license
* Documentation: https://cellmaps-utils.readthedocs.io.

Dependencies
------------

* `fairscape-cli <https://pypi.org/project/fairscape-cli>`__
* `scipy <https://pypi.org/project/scipy>`__
* `scikit-learn <https://pypi.org/project/scikit-learn>`__
* `pandas <https://pypi.org/project/pandas>`__
* `numpy <https://pypi.org/project/numpy>`__
* `dill <https://pypi.org/project/dill>`__

Compatibility
-------------

* Python 3.8+

Installation
------------

.. code-block::

   git clone https://github.com/idekerlab/cellmaps_utils
   cd cellmaps_utils
   make dist
   pip install dist/cellmaps_utils*whl


Run **make** command with no arguments to see other build/deploy options including creation of Docker image 

.. code-block::

   make

Output:

.. code-block::

   clean                remove all build, test, coverage and Python artifacts
   clean-build          remove build artifacts
   clean-pyc            remove Python file artifacts
   clean-test           remove test and coverage artifacts
   lint                 check style with flake8
   test                 run tests quickly with the default Python
   test-all             run tests on every Python version with tox
   coverage             check code coverage quickly with the default Python
   docs                 generate Sphinx HTML documentation, including API docs
   servedocs            compile the docs watching for changes
   testrelease          package and upload a TEST release
   release              package and upload a release
   dist                 builds source and wheel package
   install              install the package to the active Python's site-packages

For developers
-------------------------------------------

To deploy development versions of this package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Below are steps to make changes to this code base, deploy, and then run
against those changes.

#. Make changes

Modify code in this repo as desired

#. Build and deploy

.. code-block::

    # From base directory of this repo cellmaps_hierarchyeval
    pip uninstall cellmaps_utils -y ; make clean dist; pip install dist/cellmaps_utils*whl



Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template


.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
.. _NDEx: http://www.ndexbio.org

