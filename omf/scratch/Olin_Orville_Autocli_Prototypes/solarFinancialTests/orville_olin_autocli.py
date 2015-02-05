import sys, os
sys.path.append('../../../')
from models import __metaModel__, solarFinancial
from __metaModel__ import *
from solarFinancial import *


def _tests(companyname):
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	# No-input template.
	#renderAndShow(template)	
	# TODO: Fix inData because it's out of date.
	if ("default" in companyname):	 #confirm this is choptank
		inData = {"simStartDate": "2013-01-01",
			"simLengthUnits": "hours",
			"modelType": "solarFinancial",
			"climateName": "AL-HUNTSVILLE",
			"simLength": "8760",
			"systemSize":"100",
			"installCost":"100000",
			"lifeSpan": "30",
			"degradation": "0.5",
			"retailCost": "0.10",
			"discountRate": "0.07",
			"pvModuleDerate": "0.995",
			"mismatch": "0.995",
			"dcWiring": "0.995",
			"acWiring": "0.995",
			"soiling": "0.995",
			"shading": "0.995",
			"sysAvail": "0.995",
			"age": "0.995",
			"tilt": "False",
			"manualTilt":"34.65",			
			"srecCashFlow": "5,5,3,3,2",
			"trackingMode":"0",
			"azimuth":"180",
			"runTime": "",
			"rotlim":"45.0",
			"gamma":"-0.5",
			"omCost": "1000"}
		modelLoc = pJoin(workDir,"admin","Automated solarFinancial Testing")
		# Blow away old test results if necessary.
		try:
			shutil.rmtree(modelLoc)
		except:
			# No previous test results.
			pass
		# Run the model.
		run(modelLoc, inData)
		# Show the output.
		renderAndShow(template, modelDir = modelLoc)
		# # Delete the model.
		# time.sleep(2)
		# shutil.rmtree(modelLoc) 
	if ("orville" in companyname):	                 #Used PVSyst - MG Suniva
		inData = {"simStartDate": "2013-01-01",  #These 2 & Length should be from GLM
			"simLengthUnits": "hours",
			"modelType": "solarFinancial",
			"climateName": "MN-SAINT_CLOUD",     #Minneapolis - pick MN- Saint Cloud, doesn't work for this
			"simLength": "8760",                 ##16h25m used for PVSyst
			"systemSize":"95.4",                 #Pnom p.2
			"installCost":"362338",              #use 1MW Estimated Cost for coserv system: 9.5% of (780000+168,100)+50010+49000+19926+1000
			"lifeSpan": "30",                    #
			"degradation": "0.65",               #Suniva Datasheet: (25-12)/(10%)/2
			"retailCost": "0.099",                #
			"discountRate": "0.07",              #
			"pvModuleDerate": "0.994",           #Inverter losses: 4.9%?
			"mismatch": "0.99",                  #1%
			"dcWiring": "0.985",                 #1.5%
			"acWiring": "0.985",                 #1.5%
			"soiling": "0.99",                   #1%
			"shading": "0.995",                  #  
			"sysAvail": "0.995",                 #
			"age": "0.995",                      #
			"tilt": "False",                     #Add tilt: 20 degrees
			"manualTilt":"20",			
			"srecCashFlow": "0",         #
			"trackingMode":"0",                  #
			"azimuth":"180",                     #
			"runTime": "",                      
			"rotlim":"46.0",                     #suniva datasheet: noct?
			"gamma":"-0.42",                     #suniva
			"omCost": "1000"}	
		modelLoc = pJoin(workDir,"admin","Orville solarFinancial Testing")
		# Blow away old test results if necessary.
		try:
			shutil.rmtree(modelLoc)
		except:
			# No previous test results.
			pass
		# Run the model.
		run(modelLoc, inData)
		# Show the output.
		renderAndShow(template, modelDir = modelLoc)
		# # Delete the model.
		# time.sleep(2)
		# shutil.rmtree(modelLoc)
	if ("autocli" in companyname):	             #Using NRECA CoServ Ike Byrom - PVSyst Phase 1 V1 
		inData = {"simStartDate": "2013-01-01",  #These 2 & Length should be from GLM
			"simLengthUnits": "hours",
			"modelType": "solarFinancial",        
			"climateName": "TX-ABILENE",         #For TX Fort Worth
			"simLength": "8760",                 #
			"systemSize":"1000",                 #1MW because limited by inverter Pmax of 1MW
			"installCost":"2121046.54",          #1MW Estimated Cost.xlsx
			"lifeSpan": "30",                    #code above requires 30
			"degradation": "0.5", 				 #cant find on panel datasheet
			"retailCost": "0.085",				 #
			"discountRate": "0.07",				 #
			"pvModuleDerate": "0.995",			 #
			"mismatch": "0.995",                 #PVS
			"dcWiring": "0.985",                 #PVS
			"acWiring": "0.985",                 #Does this include transformer losses?
			"soiling": "0.97",                   #PVSyst
			"shading": "0.998",                  #Is this Shadings: electrical or Shadings Horizon/Irradiance loss?
			"sysAvail": "0.995",                 #
			"age": "0.995",                      #Different from soiling?
			"tilt": "False",                     #Add 25 deg
			"manualTilt":"25",			
			"srecCashFlow": "0",
			"trackingMode":"0",
			"azimuth":"0",                       #0
			"runTime": "",
			"rotlim":"45.0",
			"gamma":"-0.5",                      #Max power temp coefficient 25.22
			"omCost": "1000"}
		modelLoc = pJoin(workDir,"admin","Autocli solarFinancial Testing")
		# Blow away old test results if necessary.
		try:
			shutil.rmtree(modelLoc)
		except:
			# No previous test results.
			pass
		# Run the model.
		run(modelLoc, inData)
		# Show the output.
		renderAndShow(template, modelDir = modelLoc)
		# # Delete the model.
		# time.sleep(2)
		# shutil.rmtree(modelLoc)
	if ("olin" in companyname):	                 #Using oservs solar system data but half of install costs
		inData = {"simStartDate": "2013-01-01",  #These 2 & Length should be from GLM
			"simLengthUnits": "hours",
			"modelType": "solarFinancial",        
			"climateName": "KY-LEXINGTON",       #
			"simLength": "8760",                 #
			"systemSize":"1000",                 #
			"installCost":"1060523",             #
			"lifeSpan": "30",                    #
			"degradation": "0.5", 				 #
			"retailCost": "0.078",				 #
			"discountRate": "0.07",				 #
			"pvModuleDerate": "0.995",			 #
			"mismatch": "0.995",                 #
			"dcWiring": "0.985",                 #
			"acWiring": "0.985",                 #
			"soiling": "0.97",                   #
			"shading": "0.998",                  #
			"sysAvail": "0.995",                 #
			"age": "0.995",                      #
			"tilt": "False",                     #
			"manualTilt":"25",			         #
			"srecCashFlow": "0",                 #
			"trackingMode":"0",                  #
			"azimuth":"0",                       #
			"runTime": "",                       #
			"rotlim":"45.0",                     #
			"gamma":"-0.5",                      #
			"omCost": "1000"}
		modelLoc = pJoin(workDir,"admin","Olin solarFinancial Testing")
		# Blow away old test results if necessary.		
		try:
			shutil.rmtree(modelLoc)
		except:
			# No previous test results.
			pass
		# Run the model.
		run(modelLoc, inData)
		# Show the output.
		renderAndShow(template, modelDir = modelLoc)
		# # Delete the model.
		# time.sleep(2)
		# shutil.rmtree(modelLoc)
	if (len(companyname) == 0):
		pass	

if __name__ == '__main__':
	_tests("default autocli olin orville")