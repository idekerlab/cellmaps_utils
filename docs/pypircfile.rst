Expected configuration for .pypirc file
============================================

To run ``make testrelease`` or ``make release`` to deploy cellmaps_utils to TestPyPi_ & PyPi_ you must have credentials set up.

#. If not already, create account on PyPi_
#. If not already, create account on TestPyPi_
#. Create a configuration file in your home directory ``~/.pypirc`` and fill it with the following information replacing **<API TOKEN>**
   with `API TOKEN`_:

.. code-block::

    [distutils]
    index-servers=
    pypi
    testpypi

    [testpypi]
    repository:https://test.pypi.org/legacy/
    username = __token__
    password = <API TOKEN>

    [pypi]
    username: __token__
    password:<API TOKEN>

.. _TestPyPi: https://test.pypi.org
.. _PyPi: https://pypi.org
.. _`API Token`: https://pypi.org/help/#apitoken
