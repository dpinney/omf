import sys, os
sys.path.append('../..')
from models import __metaModel__, solarRates
from __metaModel__ import *
from solarRates import *


def _tests(companyname):
	# company - choptank, or coserv
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	if ("autocli" in companyname):
		monthlyData = {
		"janSale": "154491", "janKWh": 237441891.5*1.04, "janRev": 23317522.75*1.04, "janKWhT": 369382665.6*1.04, "janRevT": 33910924.5*1.04, 
		"febSale": (154491+162579)/2*random.uniform(0.95,1.05), "febKWh": 237441891.5*1.05, "febRev": 23317522.75*1.05, "febKWhT": 369382665.6*1.05, "febRevT": 33910924.5*1.05, 
		"marSale": (154491+162579)/2*random.uniform(0.95,1.05), "marKWh": 237441891.5*0.95, "marRev": 23317522.75*0.95, "marKWhT": 369382665.6*0.95, "marRevT": 33910924.5*0.95, 
		"aprSale": (154491+162579)/2*random.uniform(0.95,1.05), "aprKWh": 237441891.5*1.02, "aprRev": 23317522.75*1.02, "aprKWhT": 369382665.6*1.02, "aprRevT": 33910924.5*1.02, 
		"maySale": (154491+162579)/2*random.uniform(0.95,1.05), "mayKWh": 237441891.5*0.98, "mayRev": 23317522.75*0.98, "mayKWhT": 369382665.6*0.98, "mayRevT": 33910924.5*0.98, 
		"junSale": (154491+162579)/2*random.uniform(0.95,1.05), "junKWh": 237441891.5*1.07, "junRev": 23317522.75*1.07, "junKWhT": 369382665.6*1.07, "junRevT": 33910924.5*1.07, 
		"julSale": (154491+162579)/2*random.uniform(0.95,1.05), "julKWh": 237441891.5*0.93, "julRev": 23317522.75*0.93, "julKWhT": 369382665.6*0.93, "julRevT": 33910924.5*0.93, 
		"augSale": (154491+162579)/2*random.uniform(0.95,1.05), "augKWh": 237441891.5*1.08, "augRev": 23317522.75*1.08, "augKWhT": 369382665.6*1.08, "augRevT": 33910924.5*1.08, 
		"sepSale": (154491+162579)/2*random.uniform(0.95,1.05), "sepKWh": 237441891.5*0.92, "sepRev": 23317522.75*0.92, "sepKWhT": 369382665.6*0.92, "sepRevT": 33910924.5*0.92, 
		"octSale": (154491+162579)/2*random.uniform(0.95,1.05), "octKWh": 237441891.5*0.99, "octRev": 23317522.75*0.99, "octKWhT": 369382665.6*0.99, "octRevT": 33910924.5*0.99, 
		"novSale": (154491+162579)/2*random.uniform(0.95,1.05), "novKWh": 237441891.5*1.01, "novRev": 23317522.75*1.01, "novKWhT": 369382665.6*1.01, "novRevT": 33910924.5*1.01, 
		"decSale": "162579", "decKWh": 237441891.5*0.96, "decRev": 23317522.75*0.96, "decKWhT": 369382665.6*0.96, "decRevT": 33910924.5*0.96 }
		inData = {
			"modelType": "solarRates",
			"climateName": "TX-ABILENE",
			"runTime": "",
			# Single data point
			"avgSystemSize": "5",
			"resPenetration": "10",
			"customServiceCharge": "20",
			"solarServiceCharge": "10",		
			"solarLCoE": "0.07",                 #*missing
			"otherElecRevenue": "5638935",       #
			"totalKWhPurchased": "4599859479",   #7.R.16
			# Form 7 data
			"powerProExpense": "0",              #
			"costPurchasedPower": "286409564",   #
			"transExpense": "0",                 #
			"distriExpenseO": "6469309",         #
			"distriExpenseM": "6886801",         #
			"customerAccountExpense": "5113838", #
			"customerServiceExpense": "3335811", #
			"salesExpense": "0",                 #
			"adminGeneralExpense": "21975870",   #
			"depreAmortiExpense": "22299922",    #
			"taxExpensePG": "2355344",           #
			"taxExpense": "630630",              #
			"interestLongTerm": "25007662",      #
			"interestConstruction": "0", 	 	 #
			"interestExpense": "351550",	     #
			"otherDeductions": "0",              #
			"nonOpMarginInterest": "939288",     #
			"fundsUsedConstruc":"0",             #
			"incomeEquityInvest":"0",            #
			"nonOpMarginOther": "2736291",       #*negative value?
			"genTransCapCredits": "0",     #
			"otherCapCreditsPatroDivident": "19746046", #
			"extraItems":"0" }	
		for key in monthlyData:
			inData[key] = monthlyData[key]
		modelLoc = pJoin(workDir,"admin","Prototype Autocli solarRates")
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
	if ("orville" in companyname):
		monthlyData = {
		"janSale": (41932)*random.uniform(0.95,1.05), "janKWh": 45564364*1.04, "janRev": 5034093*1.04, "janKWhT": 75311980*1.04, "janRevT": 7605792*1.04, 
		"febSale": (41932)*random.uniform(0.95,1.05), "febKWh": 45564364*1.05, "febRev": 5034093*1.05, "febKWhT": 75311980*1.05, "febRevT": 7605792*1.05, 
		"marSale": (41932)*random.uniform(0.95,1.05), "marKWh": 45564364*0.95, "marRev": 5034093*0.95, "marKWhT": 75311980*0.95, "marRevT": 7605792*0.95, 
		"aprSale": (41932)*random.uniform(0.95,1.05), "aprKWh": 45564364*1.02, "aprRev": 5034093*1.02, "aprKWhT": 75311980*1.02, "aprRevT": 7605792*1.02, 
		"maySale": (41932)*random.uniform(0.95,1.05), "mayKWh": 45564364*0.98, "mayRev": 5034093*0.98, "mayKWhT": 75311980*0.98, "mayRevT": 7605792*0.98, 
		"junSale": (41932)*random.uniform(0.95,1.05), "junKWh": 45564364*1.07, "junRev": 5034093*1.07, "junKWhT": 75311980*1.07, "junRevT": 7605792*1.07, 
		"julSale": (41932)*random.uniform(0.95,1.05), "julKWh": 45564364*0.93, "julRev": 5034093*0.93, "julKWhT": 75311980*0.93, "julRevT": 7605792*0.93, 
		"augSale": (41932)*random.uniform(0.95,1.05), "augKWh": 45564364*1.08, "augRev": 5034093*1.08, "augKWhT": 75311980*1.08, "augRevT": 7605792*1.08, 
		"sepSale": (41932)*random.uniform(0.95,1.05), "sepKWh": 45564364*0.92, "sepRev": 5034093*0.92, "sepKWhT": 75311980*0.92, "sepRevT": 7605792*0.92, 
		"octSale": (41932)*random.uniform(0.95,1.05), "octKWh": 45564364*0.99, "octRev": 5034093*0.99, "octKWhT": 75311980*0.99, "octRevT": 7605792*0.99, 
		"novSale": (41932)*random.uniform(0.95,1.05), "novKWh": 45564364*1.01, "novRev": 5034093*1.01, "novKWhT": 75311980*1.01, "novRevT": 7605792*1.01, 
		"decSale": "42299", "decKWh": 45564364*0.96, "decRev": 5034093*0.96, "decKWhT": 75311980*0.96, "decRevT": 7605792*0.96 }
		inData = {
			"modelType": "solarRates",
			"climateName": "MN-SAINT_CLOUD",
			"runTime": "",
			# Single data point
			"avgSystemSize": "5",
			"resPenetration": "10",
			"customServiceCharge": "20",
			"solarServiceCharge": "10",		
			"solarLCoE": "0.07",                        #missing
			"otherElecRevenue": "662497",         		#
			"totalKWhPurchased": "940757466",     		#
			# Form 7 data
			"powerProExpense": "0",               		#
			"costPurchasedPower": "64285196",     		#
			"transExpense": "0",                  		#
			"distriExpenseO": "7815176",          		#
			"distriExpenseM": "2565625",          		#
			"customerAccountExpense": "1257467",  		#
			"customerServiceExpense": "1837044",  		#
			"salesExpense": "224032",             		#    
			"adminGeneralExpense": "3129392",     		#  
			"depreAmortiExpense": "4530659",      		#  
			"taxExpensePG": "0",                  		#   
			"taxExpense": "0",                    		#   	 
			"interestLongTerm": "3572043",        		#
			"interestConstruction": "0", 	 	  		#
			"interestExpense": "2120",	         		#
			"otherDeductions": "10630",          		#
			"nonOpMarginInterest": "426055",      		# 
			"fundsUsedConstruc": "0",             		#
			"incomeEquityInvest": "659919",       	   	#loss     
			"nonOpMarginOther": "497520",         	   	#loss
			"genTransCapCredits": "2707968",           	#
			"otherCapCreditsPatroDivident": "374260",  	#
			"extraItems":"0" }	
		for key in monthlyData:
			inData[key] = monthlyData[key]
		modelLoc = pJoin(workDir,"admin","Prototype Orville solarRates")
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
	if ("olin" in companyname):
		monthlyData = {
		"janSale": (55496)*random.uniform(0.95,1.05), "janKWh": 61374580*1.04, "janRev": 6619927*1.04, "janKWhT": 185459376.2*1.04, "janRevT": 14063772.08*1.04, 
		"febSale": (55496)*random.uniform(0.95,1.05), "febKWh": 61374580*1.05, "febRev": 6619927*1.05, "febKWhT": 185459376.2*1.05, "febRevT": 14063772.08*1.05, 
		"marSale": (55496)*random.uniform(0.95,1.05), "marKWh": 61374580*0.95, "marRev": 6619927*0.95, "marKWhT": 185459376.2*0.95, "marRevT": 14063772.08*0.95, 
		"aprSale": (55496)*random.uniform(0.95,1.05), "aprKWh": 61374580*1.02, "aprRev": 6619927*1.02, "aprKWhT": 185459376.2*1.02, "aprRevT": 14063772.08*1.02, 
		"maySale": (55496)*random.uniform(0.95,1.05), "mayKWh": 61374580*0.98, "mayRev": 6619927*0.98, "mayKWhT": 185459376.2*0.98, "mayRevT": 14063772.08*0.98, 
		"junSale": (55496)*random.uniform(0.95,1.05), "junKWh": 61374580*1.07, "junRev": 6619927*1.07, "junKWhT": 185459376.2*1.07, "junRevT": 14063772.08*1.07, 
		"julSale": (55496)*random.uniform(0.95,1.05), "julKWh": 61374580*0.93, "julRev": 6619927*0.93, "julKWhT": 185459376.2*0.93, "julRevT": 14063772.08*0.93, 
		"augSale": (55496)*random.uniform(0.95,1.05), "augKWh": 61374580*1.08, "augRev": 6619927*1.08, "augKWhT": 185459376.2*1.08, "augRevT": 14063772.08*1.08, 
		"sepSale": (55496)*random.uniform(0.95,1.05), "sepKWh": 61374580*0.92, "sepRev": 6619927*0.92, "sepKWhT": 185459376.2*0.92, "sepRevT": 14063772.08*0.92, 
		"octSale": (55496)*random.uniform(0.95,1.05), "octKWh": 61374580*0.99, "octRev": 6619927*0.99, "octKWhT": 185459376.2*0.99, "octRevT": 14063772.08*0.99, 
		"novSale": (55496)*random.uniform(0.95,1.05), "novKWh": 61374580*1.01, "novRev": 6619927*1.01, "novKWhT": 185459376.2*1.01, "novRevT": 14063772.08*1.01, 
		"decSale": "55444",                           "decKWh": 61374580*0.96, "decRev": 6619927*0.96, "decKWhT": 185459376.2*0.96, "decRevT": 14063772.08*0.96 }
		inData = {
			"modelType": "solarRates",
			"climateName": "KY-LEXINGTON",
			"runTime": "",
			# Single data point
			"avgSystemSize": "5",
			"resPenetration": "10",
			"customServiceCharge": "20",
			"solarServiceCharge": "10",		
			"solarLCoE": "0.07",                        #missing
			"otherElecRevenue": "2078588",         		#
			"totalKWhPurchased": "2275532176",     		#
			# Form 7 data
			"powerProExpense": "0",               		#
			"costPurchasedPower": "139857103",     		#
			"transExpense": "0",                  		#
			"distriExpenseO": "5125225",          		#
			"distriExpenseM": "3533346",          		#
			"customerAccountExpense": "3727056",  		#
			"customerServiceExpense": "647922",  		#
			"salesExpense": "0",                 		#    
			"adminGeneralExpense": "4138560",     		#  
			"depreAmortiExpense": "10990984",      		#  
			"taxExpensePG": "0",                		#   
			"taxExpense": "8646",                    	#   	 
			"interestLongTerm": "4636093",        		#
			"interestConstruction": "0", 	 	  		#
			"interestExpense": "127826",	       		#
			"otherDeductions": "101275",          		#
			"nonOpMarginInterest": "558147",      		# 
			"fundsUsedConstruc": "0",             		#
			"incomeEquityInvest": "0",       	   	    #loss     
			"nonOpMarginOther": "25929",         	   	#
			"genTransCapCredits": "9354127",           	#
			"otherCapCreditsPatroDivident": "56721",  	#
			"extraItems":"0" }	
		for key in monthlyData:
			inData[key] = monthlyData[key]
		modelLoc = pJoin(workDir,"admin","Prototype Olin solarRates")
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
	if (len(companyname) == 0):
		pass	


if __name__ == '__main__':
	_tests("chesapeake autocli olin orville")