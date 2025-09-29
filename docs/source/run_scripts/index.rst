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
