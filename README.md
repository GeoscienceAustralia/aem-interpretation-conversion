# AEM Interpretation Conversion Tool (AEMInterpConvert)

## Overview
For more information about AEMInterpConvert, Geoscience Australia’s Online Airborne Electromagnetic Interpretation Conversion Tool, see this [Geoscience Australia article](https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/150529).

---

## Installation Guide

### 1. Clone the Repository
```bash
git clone git@bitbucket.org:geoscienceaustralia/aem-interpretation-conversion.git
cd aem-interpretation-conversion
```

---

### 2. Choose Your Environment Setup

### **Option A: Anaconda (Recommended)**
If you have [Anaconda](https://www.anaconda.com/download) installed:
```bash
conda env create -f environment.yml
conda activate aemworkflow-env
```

---

### **Option B: Python 3.12 + Virtual Environment (VENV)**  
#### i. Ensure Python 3.12 is installed.

**Linux / macOS:**
```bash
python3.12 -m venv aem-venv
source aem-venv/bin/activate
```

**Windows (Command Prompt):**
```powershell
python -m venv aem-venv
aem-venv\Scripts\activate.bat
```

#### ii. Install GDAL Dependencies.

**Linux / macOS:**
Use the provided build script to install system-level GDAL and PROJ libraries:
```bash
cd builds
./linux_gdal.sh
```

This script will:
- Install required system packages (`gdal`, `proj`)  
- Install the Python GDAL bindings matching your GDAL version  

---

**Windows**
1. Download and install [OSGeo4W](https://trac.osgeo.org/osgeo4w/).  
   - Choose **Advanced Install**  
   - Select the following packages:  
     - `gdal`  
     - `proj`

2. After installation (default path is `C:\OSGeo4W` or `C:\OSGeo4W64`), run the helper script to configure environment variables and install Python GDAL bindings using Windows Command prompt (CMD):
```cmd
cd builds
windows_gdal.bat
```

This script will:
- Add OSGeo4W binaries to your `PATH`
- Detect the installed GDAL version (`gdalinfo --version`)
- Install the matching Python GDAL bindings via `pip`

---


#### iii. Install the AEMInterpConvert Package

After setting up dependencies:
```bash
pip install .
```

---

#### iiii. Verify GDAL Installation
To confirm GDAL bindings are working correctly:
```bash
python -c "from osgeo import gdal; print(gdal.VersionInfo())"
```

#### iiiii. Add current directory to your PYTHONPATH
```bash
export PYTHONPATH=${cloned_directory}
```

### 3. CLI Usage
------------
For each script, run the file with any required arguments and any additional where you want to deviate from the default. All arguments should be in quotes as per the examples.  

If using Anaconda, activate conda environment if required before running the scripts.  

Navigate to the folder where the scripts are located
```
cd aemworkflow
```

### Pre-interpretation

```
python pre_interpretation.py -i "{input_directory}" -o "{output_directory}
```

**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|   |
| -g          | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|   |
| -l          | depth lines     | No           |10         |          |        |
| -li         | depth lines increment| No      |30         |          |        |

### Interpretation

```
python interpretation.py -i "{input_directory}" -o "{output_directory}"
```
**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |  |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|  |
| -g          | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|  |
| -l          | depth lines     | No           |10         |          |  |
| -li         | depth lines increment| No      |30         |          |  |

### Validation

```
python validation.py -i "{input_directory}" -o "{output_directory}" -a "{asud_filename}"
```
**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -a          | ausd file name  | Yes          |None       |          |        |


### Conversion

```
python conversion.py -i "{input_directory}" -o "{output_directory}"
```
**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|        |


### Export

```
python exports.py -i "{input_directory}" -o "{output_directory}" -m "y" -mh "n" -e "n" -b "{boundary_file}" -s "{split_file}"
```
**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
| -i          | input directory | Yes          |None       |          |A non zipped folder containing required files|
| -o          | output directory| Yes          |None       |          |        |
| -m          | Export to MDC format| Yes      |None       |y or n    |        |
| -mh         | Export to MDCH format| Yes     |None       |y or n    |        |
| -e          | Export to EGS format| Yes      |None       |y or n    |        |
| -b          | name of boundary file| Yes     |None       |          |        |
| -s          | name of split file   | Yes     |None       |          |        |

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
