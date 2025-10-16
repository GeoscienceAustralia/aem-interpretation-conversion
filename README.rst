AEM Interpretation Conversion Tool (AEMInterpConvert)
================================================================

Background
==========

In response to the acquisition of national-scale airborne electromagnetic surveys and the development of a national depth estimates database, a new workflow has been established to interpret airborne electromagnetic conductivity sections. This workflow allows for high quantities of high quality interpretation-specific metadata to be attributed to each interpretation line or point. The conductivity sections are interpreted in 2D space, and are registered in 3D space using code developed at Geoscience Australia. This code also verifies stratigraphic unit information against the national Australian Stratigraphic Units Database, and extracts interpretation geometry and geological data, such as depth estimates compiled in the Estimates of Geological and Geophysical Surfaces database. Interpretations made using this workflow are spatially consistent and contain large amounts of useful stratigraphic unit information. These interpretations are made freely-accessible as

1) Text files and 3D objects through an electronic catalogue, 
2) As point data through a point database accessible via a data portal, and 
3) Available for 3D visualisation and interrogation through a 3D data portal.

These precompetitive data support the construction of national 3D geological architecture models, including cover and basement surface models, and resource prospectivity models. These models are in turn used to inform academia, industry and governments on decision-making, land use, environmental management, hazard mapping, and resource exploration.

For more information please see the `Metadata Statement and User Guide`_ and `Workflow Document`_.

.. _Metadata Statement and User Guide: https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/150529

.. _Workflow Document: https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/147251


Installation
============

1. Clone the Repository
-------------------------------
.. code-block:: bash

    git clone https://github.com/GeoscienceAustralia/aem-interpretation-conversion.git
    cd aem-interpretation-conversion

---

2. Choose Your Environment Setup
--------------------------------------


**Option A: Anaconda (Recommended)**
----------------------------------------------

If you have `Anaconda`_ installed

.. _Anaconda: https://www.anaconda.com/downloads

.. code-block:: bash

    conda env create -f environment.yml
    conda activate aemworkflow-env


**Option B: Python 3.12 + Virtual Environment (VENV)**  
----------------------------------------------
Install a virtual environment
--------------------------------

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

Continue with the verification and installation instructions below

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

Continue with the verification and installation instructions below

.. _verification-and-installation:

Verification and installation
----------------

Then verify the gdal installation and bindings are working correctly by ensuring this command runs without errors:

.. code-block:: bash
    python -c "from osgeo import gdal; print(gdal.VersionInfo())"

Finally, install the AEMInterpConvert Package:

.. code-block:: bash

    pip install .


Run scripts
============

For each script, run the file with any required arguments and any additional where you want to deviate from the default. All arguments should be in quotes as per the examples.  

If using Anaconda, activate conda environment if required before running the scripts.  

Pre-interpretation
-----------------------


.. code-block:: bash

    aemworkflow pre-interpret --i "{input_directory}" --o "{output_directory}" 


**Parameter examples:**


============================= ============== =============== ================================================ =============================================
Argument                      Required       Default         Options                                          Notes    
============================= ============== =============== ================================================ =============================================
input directory               Yes            None                                                             A non zipped folder containing required files 
output directory              Yes            None                                                                    
coordinate reference system   No             28349           28349, 28350, 28351, 28352, 28354, 28355, 28356  GDA/MGA zone EPSG
GIS software                  No             Esri ArcMap     esri_arcmap_0.5 or esri_arcmap_pro_0.5     
number of depth lines         No             10                              
lines increments in metres    No             30          
============================= ============== =============== ================================================ =============================================                    

Interpretation
-----------------------


.. code-block:: bash

    aemworkflow interpret --i "{input_directory}" --o "{output_directory}" 

**Parameter examples:**

============================= ============== =============== ================================================ =============================================
Argument                      Required       Default         Options                                          Notes    
============================= ============== =============== ================================================ =============================================
input directory               Yes            None                                                             A non zipped folder containing required files 
output directory              Yes            None                                                                    
coordinate reference system   No             28349           28349, 28350, 28351, 28352, 28354, 28355, 28356  GDA/MGA zone EPSG
GIS software                  No             Esri ArcMap     esri_arcmap_0.5 or esri_arcmap_pro_0.5     
number of depth lines         No             10                              
lines increments in metres    No             30          
============================= ============== =============== ================================================ =============================================                  

Validation
-----------------------

.. code-block:: bash

    aemworkflow validate --i "{input_directory}" --o "{output_directory}" --a "{asud_filename}"

**Parameter examples:**

============================= ============== =============== ========= =============================================
Argument                      Required       Default         Options   Notes    
============================= ============== =============== ========= =============================================
input directory               Yes            None                      A non zipped folder containing required files 
output directory              Yes            None                             
asud filename                 Yes            None
============================= ============== =============== ========= =============================================    

Conversion
-----------------------

.. code-block:: bash

    aemworkflow convert --i "{input_directory}" --o "{output_directory}" 

**Parameter examples:**

============================= ============== =============== ================================================ =============================================
Argument                      Required       Default         Options                                          Notes    
============================= ============== =============== ================================================ =============================================
input directory               Yes            None                                                             A non zipped folder containing required files 
output directory              Yes            None                                                                    
coordinate reference system   No             28349            28349, 28350, 28351, 28352, 28354, 28355, 28356 GDA/MGA zone EPSGac
============================= ============== =============== ================================================ =============================================


Export
-----------------------

.. code-block:: bash

    aemworkflow export --i "{input_directory}" --o "{output_directory}" --b "{boundary_file}" --s "{split_file}" --mdc --mdch --egs 

**Parameter examples:**

============================= ============== =============== ================================================ =============================================
Argument                      Required       Default         Options                                          Notes    
============================= ============== =============== ================================================ =============================================
input directory               Yes            None                                                             A non zipped folder containing required files 
output directory              Yes            None                                                                    
asud filename                 Yes            None
boundary file                 Yes            None                                                            
split file                    No             None                                                   
--mdc                         No             False            Add the flag if you want to set to true         Export to MDC format
--mdch                        No             False            Add the flag if you want to set to true         Export to MDCH format
--egs                         No             False            Add the flag if you want to set to true         Export to EGS format
============================= ============== =============== ================================================ =============================================           



Useful Links
------------

Home Page
    http://github.com/GeoscienceAustralia/aem-interpretation-conversion

Documentation
    http://GeoscienceAustralia.github.io/aem-interpretation-conversion

Issue tracking
    https://github.com/GeoscienceAustralia/aem-interpretation-conversion/issues

AEMInterpConvert website user interface https://aem.toolkits.ga.gov.au

Bugs & Feedback
---------------

For bugs, questions and discussions, please use  
Github Issues https://github.com/GeoscienceAustralia/aem-interpretation-conversion/issues
