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
```
conda init
conda env -create -f environment.yml
conda activate aemworkflow-scripts
```

#### For Linux users  
Install gdal, python and pip versions listed in environment.yml  
Pip install packages and versions listed in environment.yml

CLI Usage
------------
Follow conda environment setup instructions first. Once the conda environment is activated:

`python aemworkflow/pre_interpretation.py -i "{input_directory}" -o "{output_directory}"`

`python aemworkflow/interpretation.py -i "{input_directory}" -o "{output_directory}"`

`python aemworkflow/validation.py -i "{input_directory}" -o "{output_directory}" -a "{asud_filename}"`

`python aemworkflow/conversion.py -i "{input_directory}" -o "{output_directory}"`  
#### Export options:  
-m export to MDC format, y or n  
-mh export to MDCH format, y or n  
-e export to EGS format, y or n  
-b boundary file  
-s split file  
-n comma separated list of name numbers  
`python aemworkflow/exports.py -i "{input_directory}" -o "{output_directory}" -m "y" -mh "n" -e "n" -b "{boundary_file}" -s "{split_file}" -n "{comma_separated_list_of_name_numbers}"`

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