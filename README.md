# AEM interpretation conversion workflow

AEM Interpretation Conversion Tools


Setup
------------
```
git clone git@bitbucket.org:geoscienceaustralia/aem-interpretation-conversion.git
cd aem-interpretation-conversion
```
#### For Windows users:  
If you do not have Anaconda already installed, run the build_environment.sh script in your compatible environment (eg Git Bash)  
`bash build_environment.sh`  

If you already have Anaconda installed, run the following commands:  
`conda init`  
`conda env -create -f environment.yml`  

You will only need to create/build the conda environment once.

#### For Linux users  
Install gdal, python and pip versions listed in environment.yml  
Pip install packages and versions listed in environment.yml

CLI Usage
------------
Follow conda environment setup instructions first. If you have already setup the conda environment previously then run:  
`conda activate aemworkflow-scripts`  

For each script, run the file with any required arguments and any additional where you want to deviate from the default. All arguments should be in quotes as per the examples.  

### Pre-interpretation
 
| Flag        | Argument        | Required     | Default   |Options   |
| ------------|-----------------| ------------ |-----------|----------|
| -i          | input directory | Yes          |None       |          |
| -o          | output directory| Yes          |None       |          |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|
| -g          | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|
| -l          | depth lines     | No           |10         |          |
| -li         | depth lines increment| No      |30         |          |

`python aemworkflow/pre_interpretation.py -i "{input_directory}" -o "{output_directory}"`

### Interpretation
| Flag        | Argument        | Required     | Default   |Options   |
| ------------|-----------------| ------------ |-----------|----------|
| -i          | input directory | Yes          |None       |          |
| -o          | output directory| Yes          |None       |          |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|
| -g          | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|
| -l          | depth lines     | No           |10         |          |
| -li         | depth lines increment| No      |30         |          |

`python aemworkflow/interpretation.py -i "{input_directory}" -o "{output_directory}"`

### Validation
| Flag        | Argument        | Required     | Default   |Options   |
| ------------|-----------------| ------------ |-----------|----------|
| -i          | input directory | Yes          |None       |          |
| -o          | output directory| Yes          |None       |          |
| -a          | ausd file name  | Yes          |None       |          |

`python aemworkflow/validation.py -i "{input_directory}" -o "{output_directory}" -a "{asud_filename}"`

### Conversion
| Flag        | Argument        | Required     | Default   |Options   |
| ------------|-----------------| ------------ |-----------|----------|
| -i          | input directory | Yes          |None       |          |
| -o          | output directory| Yes          |None       |          |
| -c          | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|

`python aemworkflow/conversion.py -i "{input_directory}" -o "{output_directory}"`  

### Export
| Flag        | Argument        | Required     | Default   |Options   |
| ------------|-----------------| ------------ |-----------|----------|
| -i          | input directory | Yes          |None       |          |
| -o          | output directory| Yes          |None       |          |
| -m          | Export to MDC format| Yes      |None       |y or n    |
| -mh         | Export to MDCH format| Yes     |None       |y or n    |
| -3          | Export to EGS format| Yes      |None       |y or n    |
| -b          | name of boundary file| Yes     |None       |          |
| -s          | name of split file   | Yes     |None       |          |

`python aemworkflow/exports.py -i "{input_directory}" -o "{output_directory}" -m "y" -mh "n" -e "n" -b "{boundary_file}" -s "{split_file}"`

Useful Links
------------

Home Page
    http://github.com/GeoscienceAustralia/aem-interpretation-conversion

Documentation
    http://GeoscienceAustralia.github.io/aem-interpretation-conversion

Issue tracking
    https://github.com/GeoscienceAustralia/aem-interpretation-conversion/issues


Bugs & Feedback
---------------

For bugs, questions and discussions, please use  
Github Issues <https://github.com/GeoscienceAustralia/aem-interpretation-conversion/issues>