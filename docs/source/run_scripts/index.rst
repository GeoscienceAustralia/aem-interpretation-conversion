Run Scripts
============

For each script, run the file with any required arguments and any additional where you want to deviate from the default. All arguments should be in quotes as per the examples.  

If using Anaconda, activate conda environment if required before running the scripts.  

### Pre-interpretation

.. code-block:: bash
    aemworkflow pre_interpret "{input_directory}" "{output_directory}" 

**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
|             | input directory | Yes          |None       |          |A non zipped folder containing required files|
|             | output directory| Yes          |None       |          |        |
|             | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|   |
|             | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|   |
|             | depth lines     | No           |10         |          |        |
|             | depth lines increment| No      |30         |          |        |

### Interpretation

.. code-block:: bash
    aemworkflow interpret "{input_directory}" "{output_directory}"

**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
|             | input directory | Yes          |None       |          |A non zipped folder containing required files|
|             | output directory| Yes          |None       |          |  |
|             | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|  |
|             | Interpretation GIS software| No|esri_arcmap_0.5|esri_arcmap_0.5 or esri_arcmap_pro_0.5|  |
|             | depth lines     | No           |10         |          |  |
|             | depth lines increment| No      |30         |          |  |

### Validation

.. code-block:: bash
    aemworkflow validate "{input_directory}" "{output_directory}" "{asud_filename}"

**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
|             | input directory | Yes          |None       |          |A non zipped folder containing required files|
|             | output directory| Yes          |None       |          |        |
|             | ausd file name  | Yes          |None       |          |        |


### Conversion

.. code-block:: bash
    aemworkflow convert "{input_directory}" "{output_directory}"

**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
|             | input directory | Yes          |None       |          |A non zipped folder containing required files|
|             | output directory| Yes          |None       |          |        |
|             | crs - GDA/MGA zone EPSG| No    |28349      |28349, 28350, 28351, 28352, 28354, 28355, 28356|        |


### Export

.. code-block:: bash
    aemworkflow export "{input_directory}" "{output_directory}" "{boundary_file}" "{split_file}" -mdc -mdch -egs 

**Parameter examples:**

| Flag        | Argument        | Required     | Default   |Options   |Notes   |
| ------------|-----------------| ------------ |-----------|----------|--------|
|             | input directory | Yes          |None       |          |A non zipped folder containing required files|
|             | output directory| Yes          |None       |          |        |
|             | name of boundary file| Yes     |None       |          |        |
|             | name of split file   | Yes     |None       |          |        |
| -mdc        | Export to MDC format | Yes     |False      |          |        |
| -mdch       | Export to MDCH format| Yes     |False      |          |        |
| -egs        | Export to EGS format | Yes     |False      |          |        |
