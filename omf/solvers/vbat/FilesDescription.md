Description of each file and its purpose:
Flow_raw_1minute_BPA.csv:
File holding water flow values for the VB_core_WH.m function

geodata.mat:
Matrix holding state in the first column and the city in the second. used to index TMY3 data

outdoor_temperature.csv:
The first column holds an index from 1 to 8760
The second column holds 8760 temperature data points that correspond to the 'default' input

outdoor_temperature_zipCode_94128.csv:
The first column holds an index from 1 to 8760
The second column holds 8760 temperature data points that correspond to the 94128 zipcode

outdoor_temperature_zipCode_97218.csv:
The first column holds an index from 1 to 8760
The second column holds 8760 temperature data points that correspond to the 97218 zipcode

outdoor_temperature_zipCode_98158.csv:
The first column holds an index from 1 to 8760
The second column holds 8760 temperature data points that correspond to the 98158 zipcode

temp.csv:
holds all the TMY3 data in a 8760 by 1020 matrix. This is index using geodata.mat

VB_core_TCL.m:
Child function that runs the VBAT process for AC, Fridges, and Heat Pumps

VB_core_WH.m:
Child function that runs the VBAT process for Water Heaters

VB_func.m:
Parent function that handles the inputs and prepares them and selects the proper child function

VB_test.m:
Test suite that shows different possible inputs for VB_func.

VB_TMY3.m:
This function is called in VB_func.m and takes a city as an input and returns temperature data from temp.csv