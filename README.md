# AEM interpretation conversion tool (AEMInterpConvert)


Info
------------
For more information about **AEMInterpConvert**, Geoscience Australia’s Online Airborne Electromagnetic Interpretation Conversion Tool, see this [article](https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/150529).


Installation
------------
Clone the repository

```
git clone git@bitbucket.org:geoscienceaustralia/aem-interpretation-conversion.git
cd aem-interpretation-conversion
```

### Anaconda installation
If you have Anaconda installed, you may use the following to create the environment:

```
conda init
conda env create -f environment.yml
conda activate aemworkflow-env
```
However if you don't use Anaconda:

### Linux (Python 3.12 + venv) ###
Pre-requisites:  
- Python 3  
```
python --version
python -m venv aem-venv
source aem-venv/bin/activate
sh linux_gdal.sh           # Install GDAL binaries
pip install .
```

### Windows (Python 3.12 + venv) ###
Pre-requisites:  
- Python 3  
- GDAL

#### GDAL installation instructions

1. Download and install [OSGeo4W](https://trac.osgeo.org/osgeo4w/) (Recommended)

2. During installation choose `Advanced Install` and select Libs `gdal` and `proj`

3. Finish installation (default path is `C:\OSGeo4W` or `C:\OSGeo4W64`) and set environment variables using CMD

```
set PATH=C:\OSGeo4W\bin;%PATH%
set GDAL_DATA=C:\OSGeo4W\share\gdal
set PROJ_LIB=C:\OSGeo4W\share\proj
pip install "gdal==3.8.5"       # You must change this to your version of GDAL
```

Finally install the package

```
pip install .
```

CLI Usage
------------
For each script, run the file with any required arguments and any additional where you want to deviate from the default. All arguments should be in quotes as per the examples.  

If using Anaconda, activate conda environment if required before running the scripts.  

### Pre-interpretation
 
| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|   |
| -g          | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|   |
| -l          | depth lines     | No           |10         |          |        |
| -li         | depth lines increment| No      |30         |          |        |

Anaconda command: `python aemworkflow\pre_interpretation.py -i "{input_directory}" -o "{output_directory}"`  
Pip package command: `python -m aemworkflow.pre_interpretation -i "{input_directory}" -o "{output_directory}"`

### Interpretation
| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |  |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|  |
| -g          | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|  |
| -l          | depth lines     | No           |10         |          |  |
| -li         | depth lines increment| No      |30         |          |  |


Anaconda command: `python aemworkflow\interpretation.py -i "{input_directory}" -o "{output_directory}"`  
Pip package command: `python -m aemworkflow.interpretation -i "{input_directory}" -o "{output_directory}"`


### Validation
| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -a          | ausd file name  | Yes          |None       |          |        |


Anaconda command: `python aemworkflow\validation.py -i "{input_directory}" -o "{output_directory}" -a "{asud_filename}"`  
Pip package command: `python -m aemworkflow.validation -i "{input_directory}" -o "{output_directory}" -a "{asud_filename}"`

### Conversion
| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|        |


Anaconda command: `python aemworkflow\conversion.py -i "{input_directory}" -o "{output_directory}"`  
Pip package command: `python -m aemworkflow.conversion -i "{input_directory}" -o "{output_directory}"`  

### Export
| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -m          | Export to MDC format| Yes      |None       |y or n    |        |
| -mh         | Export to MDCH format| Yes     |None       |y or n    |        |
| -e          | Export to EGS format| Yes      |None       |y or n    |        |
| -b          | name of boundary file| Yes     |None       |          |        |
| -s          | name of split file   | Yes     |None       |          |        |

Anaconda command: `python aemworkflow\exports.py -i "{input_directory}" -o "{output_directory}" -m "y" -mh "n" -e "n" -b "{boundary_file}" -s "{split_file}"`  
Pip package command: `python -m aemworkflow.exports -i "{input_directory}" -o "{output_directory}" -m "y" -mh "n" -e "n" -b "{boundary_file}" -s "{split_file}"`

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
Github Issues <https://github.com/GeoscienceAustralia/aem-interpretation-conversion/issues>