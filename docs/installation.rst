.. note:: 
    svsfunc is currently not available on PyPi as it is still in prototyping phase

Installing with pip
-------------------
To install svsfunc, use the command:

.. code-block:: bash

    python3 -m pip install git+https://github.com/Shiginn/svsfunc


If you are want to upgrade from an older version, the safest way is to uninstall and reinstall the package.
You can also try this command:

.. warning:: This will also reinstall all the dependencies, including the VapourSynth python package.
    Having mismatched VapourSynth versions can cause issues.

.. code-block:: bash

    python3 -m pip install git+https://github.com/Shiginn/svsfunc --force-reinstall


Dependencies
------------
This packages depends on `vsjetpack <https://github.com/Jaded-Encoding-Thaumaturgy/vs-jetpack>`_  and `vsmuxtools <https://github.com/Vodes/vs-muxtools>`_.
Make sure their dependencies are installed or you might experience issues.