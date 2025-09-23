.. _install_venv:

Install a virtual environment
==============

Ensure Python 3.12 is installed on your system. 
You can download it from the official Python website: https://www.python.org/downloads/.

.. _Linux/MacOS instructions:

Linux/MacOS instructions
----------------
To create a virtual environment, open a terminal and run the following commands:

.. code-block:: bash

    python3.12 -m venv aem-venv
    source aem-venv/bin/activate

This will create a virtual environment named `aem-venv` and activate it.

Then install the GDAL dependencies:
Use the provided build script to install system-level GDAL and PROJ libraries:

.. code-block:: bash

    ./builds/linux_gdal.sh

This script will:

- Install required system packages (gdal, proj)
- Install the Python GDAL bindings matching your GDAL version

And add the current directory to the Python path:

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:$(pwd)

Continue with the :ref:`verification-and-installation` instructions below

.. _Windows instructions:

Windows instructions
----------------
To create a virtual environment, open a terminal and run the following commands:

.. code-block:: bash
    python -m venv aem-venv
    aem-venv\Scripts\activate.bat

Download and install `OSGeo4W`_.

.. _OSGeo4W: https://trac.osgeo.org/osgeo4w/

- Choose Advanced Install
- Select the following packages:
    - gdal
    - proj
After installation (default path is C:\OSGeo4W or C:\OSGeo4W64), run the helper script to configure environment variables and install Python GDAL bindings using Windows Command prompt (CMD):

.. code-block:: bash

    cd builds
    windows_gdal.bat

This script will:

- Add OSGeo4W binaries to your PATH
- Detect the installed GDAL version (gdalinfo --version)
- Install the matching Python GDAL bindings via pip

Continue with the :ref:`verification-and-installation` below

.. _verification-and-installation:

Verification and installation
----------------
Then verify the gdal installation and bindings are working correctly by ensuring this command runs without errors:

.. code-block:: bash
    python -c "from osgeo import gdal; print(gdal.VersionInfo())"

Finally, install the AEMInterpConvert Package:

.. code-block:: bash

    pip install .