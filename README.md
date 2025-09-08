# AEM interpretation conversion workflow

AEM Interpretation Conversion Tools


Setup
------------
`git clone git@bitbucket.org:geoscienceaustralia/aem-interpretation-conversion.git`


CLI Usage
------------
`python aemworkflow/pre_interpretation.py -i "{input_directory}" -o "{output_directory}"`

`python aemworkflow/interpretation.py -i "{input_directory}" -o "{output_directory}"`

`python aemworkflow/validation.py -i "{input_directory}" -o "{output_directory}" -a "{asud_filename}"`

`python aemworkflow/conversion.py -i "{input_directory}" -o "{output_directory}" -m "y" -mh "n" -e "n" -b "{boundary_file}" -s "{split_file}"`

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
`Github Issues <https://github.com/GeoscienceAustralia/aem-interpretation-conversion/issues>`_.