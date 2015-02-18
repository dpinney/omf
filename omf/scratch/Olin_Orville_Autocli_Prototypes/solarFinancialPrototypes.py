import sys, os
sys.path.append('../..')
from models import __metaModel__, solarFinancial
from __metaModel__ import *
from solarFinancial import *

def _tests(companyname):
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	# No-input template.
	#renderAndShow(template)	
	if ("orville" in companyname):	             #Most data from PVSyst - MG Suniva
		inData = {"simStartDate": "2013-01-01",  
			"simLengthUnits": "hours",
			"modelType": "solarFinancial",
			"climateName": "MN-SAINT_CLOUD",     #Pick for Minneapolis
			"simLength": "8760",                 #16h25m in PVSyst
			"systemSize":"95.4",                 #Pnom p.2 (9.5% of coserv system)
			"installCost":"362338",              #Taken as 9.5% of 1MW coserv system 
			"lifeSpan": "30",                    #
			"degradation": "0.65",               #Suniva Datasheet (SD) Linear Relation: (25-12)/(10%)/2
			"retailCost": "0.099",               #solarRates
			"discountRate": "7",                 
			"pvModuleDerate": "97",              
			"mismatch": "99",                    #PVS 1%
			"diodes": "99.5",				
			"dcWiring": "98.5",                  #PVS 1.5%
			"acWiring": "98.5",                  #PVS 1.5%
			"soiling": "99",                     #PVS 1%
			"shading": "99.5",                   #PVS 0% 
			"sysAvail": "99.5",                  
			"age": "99.5",                       
			"inverterEff": "95.1",               #Inverter losses: 4.9%, 4% combined with transformer http://www.gosolarcalifornia.ca.gov/equipment/inverters.php
			"inverterSize": "100",				 #PVS		 
			"tilt": "False",                     #PVS
			"manualTilt":"20",			         #PVS: 20 degrees
			"srecCashFlow": "0",                 
			"trackingMode":"0",                  
			"azimuth":"180",                     
			"runTime": "",                      
			"rotlim":"46.0",                     #SD: noct
			"gamma":"-0.42",                     #SD
			"omCost": "1000"}	
		modelLoc = pJoin(workDir,"admin","Prototype Orville solarFinancial")
		try:
			shutil.rmtree(modelLoc)
		except:
			pass
		run(modelLoc, inData)
		renderAndShow(template, modelDir = modelLoc)
	if ("autocli" in companyname):	             #PVSYS CoServ Ike Byrom - PVSyst Phase 1 V1 
		inData = {"simStartDate": "2013-01-01", 
			"modelType": "solarFinancial",        
			"climateName": "TX-ABILENE",         #For TX Fort Worth
			"simLength": "8760",                 
			"systemSize":"1358",                 #PVS
			"installCost":"2121046.54",          #1MW Estimated Cost.xlsx
			"lifeSpan": "30",                    
			"degradation": "0.5", 				 
			"retailCost": "0.085",				 #solarRates
			"discountRate": "7",				 
			"pvModuleDerate": "98",			     #SW Datasheet (SWD)
			"diodes": "99.5",
			"mismatch": "99.5",                  #PVS
			"dcWiring": "98.5",                  #PVS: total wiring losses
			"acWiring": "98.5",                  #PVS: total wiring losses
			"soiling": "97",                     #PVS
			"shading": "98.1",                   #1.9%: All shadings on loss diagram
			"sysAvail": "99.5",                  
			"age": "99.5",                       
			"inverterEff": "98",                 #PVS Loss Diagram: Doesn't include Transf losses
			"inverterSize": "1000",				 					
			"tilt": "False",                     #
			"manualTilt":"25",			         #PVS 
			"srecCashFlow": "0",
			"trackingMode":"0",
			"azimuth":"0",                       #PVS
			"runTime": "",
			"rotlim":"45.0",
			"gamma":"-0.5",                       
			"omCost": "1000"}
		modelLoc = pJoin(workDir,"admin","Prototype Autocli solarFinancial")
		try:
			shutil.rmtree(modelLoc)
		except:
			pass
		run(modelLoc, inData)
		renderAndShow(template, modelDir = modelLoc)
	if ("olin" in companyname):	                 #Based on coserv data but half of costs
		inData = {"simStartDate": "2013-01-01",  
			"simLengthUnits": "hours",
			"modelType": "solarFinancial",        
			"climateName": "KY-LEXINGTON",       #Kentucky
			"simLength": "8760",                 
			"systemSize":"679",                  #Half size
			"installCost":"1060523",             #Half cost
			"lifeSpan": "30",                    
			"degradation": "0.5", 				 
			"retailCost": "0.085",				 #solarRates
			"discountRate": "7",				 
			"pvModuleDerate": "98",			     #SW Datasheet (SWD)
			"diodes": "99.5",
			"mismatch": "99.5",                  #PVS
			"dcWiring": "98.5",                  #PVS: total wiring losses
			"acWiring": "98.5",                  #PVS: total wiring losses
			"soiling": "97",                     #PVS
			"shading": "98.1",                   #1.9%: All shadings on loss diagram
			"sysAvail": "99.5",                  
			"age": "99.5",                       
			"inverterEff": "98",                 #PVS Loss Diagram: Doesn't include Transf losses
			"inverterSize": "500",				 					
			"tilt": "False",                     #
			"manualTilt":"25",			         #PVS 
			"srecCashFlow": "0",
			"trackingMode":"0",
			"azimuth":"0",                       #PVS
			"runTime": "",
			"rotlim":"45.0",
			"gamma":"-0.5",                       
			"omCost": "1000"}
		modelLoc = pJoin(workDir,"admin","Prototype Olin solarFinancial")
		try:
			shutil.rmtree(modelLoc)
		except:
			pass
		run(modelLoc, inData)
		renderAndShow(template, modelDir = modelLoc)

if __name__ == '__main__':
	_tests("autocli orville olin")