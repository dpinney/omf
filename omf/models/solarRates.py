''' Calculate solar photovoltaic system output using our special financial model. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, math, datetime as dt
from os.path import join as pJoin
from jinja2 import Template
import __metaModel__
from __metaModel__ import *
from operator import sub
# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"solarRates.html"),"r") as tempFile:
	template = Template(tempFile.read())

def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Check whether model exist or not
	if not os.path.isdir(modelDir):
		os.makedirs(modelDir)
		inputDict["created"] = str(dt.datetime.now())
	# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
	with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
		json.dump(inputDict, inputFile, indent = 4)
	# Copy spcific climate data into model directory
	shutil.copy(pJoin(__metaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"), 
		pJoin(modelDir, "climate.tmy2"))
	# Ready to run
	startTime = dt.datetime.now()
	# Set up SAM data structures.
	ssc = nrelsam.SSCAPI()
	dat = ssc.ssc_data_create()
	# Required user inputs.
	ssc.ssc_data_set_string(dat, "file_name", modelDir + "/climate.tmy2")
	# TODO: FIX THIS!!!! IT SHOULD BE AVGSYS*PEN*RESCUSTOMERS
	ssc.ssc_data_set_number(dat, "system_size", float(inputDict["avgSystemSize"]))
	# SAM options where we take defaults.
	ssc.ssc_data_set_number(dat, "derate", 0.97)
	ssc.ssc_data_set_number(dat, "track_mode", 0)
	ssc.ssc_data_set_number(dat, "azimuth", 180)
	ssc.ssc_data_set_number(dat, "tilt_eq_lat", 1)
	# Run PV system simulation.
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)
	# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html
	startDateTime = "2013-01-01 00:00:00 UTC"
	# Timestamp output.
	outData = {}
	outData["timeStamps"] = [dt.datetime.strftime(
		dt.datetime.strptime(startDateTime[0:19],"%Y-%m-%d %H:%M:%S") + 
		dt.timedelta(**{"hours":x}),"%Y-%m-%d %H:%M:%S") + " UTC" for x in range(int(8760))]
	# Geodata output.
	outData["city"] = ssc.ssc_data_get_string(dat, "city")
	outData["state"] = ssc.ssc_data_get_string(dat, "state")
	outData["lat"] = ssc.ssc_data_get_number(dat, "lat")
	outData["lon"] = ssc.ssc_data_get_number(dat, "lon")
	outData["elev"] = ssc.ssc_data_get_number(dat, "elev")
	# Weather output.
	outData["climate"] = {}
	outData["climate"]["Direct Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "dn")
	outData["climate"]["Difuse Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "df")
	outData["climate"]["Ambient Temperature (F)"] = ssc.ssc_data_get_array(dat, "tamb")
	outData["climate"]["Cell Temperature (F)"] = ssc.ssc_data_get_array(dat, "tcell")
	outData["climate"]["Wind Speed (m/s)"] = ssc.ssc_data_get_array(dat, "wspd")
	# Power generation.
	outData["powerOutputAc"] = ssc.ssc_data_get_array(dat, "ac")
	# Monthly aggregation outputs.
	months = {"Jan":0,"Feb":1,"Mar":2,"Apr":3,"May":4,"Jun":5,"Jul":6,"Aug":7,"Sep":8,"Oct":9,"Nov":10,"Dec":11}
	totMonNum = lambda x:sum([z for (y,z) in zip(outData["timeStamps"], outData["powerOutputAc"]) if y.startswith(startDateTime[0:4] + "-{0:02d}".format(x+1))])
	outData["monthlyGeneration"] = [[a, roundSig(totMonNum(b),2)] for (a,b) in sorted(months.items(), key=lambda x:x[1])]
	monthlyNoConsumerServedSales = []
	monthlyKWhSold = []
	monthlyRevenue = []
	totalKWhSold = []
	totalRevenue = []
	for key in inputDict:
		# MAYBEFIX: data in list may not be ordered by month.
		if key.endswith("Sale"):
			monthlyNoConsumerServedSales.append([key[:3].title(),float(inputDict.get(key, 0))])
		elif key.endswith("KWh"):# the order of calculation matters
			monthlyKWhSold.append([key[:3].title(),float(inputDict.get(key, 0))])
		elif key.endswith("Rev"):
			monthlyRevenue.append([key[:3].title(),float(inputDict.get(key, 0))])
		elif key.endswith("KWhT"):
			totalKWhSold.append([key[:3].title(),float(inputDict.get(key, 0))])
		elif key.endswith("RevT"):
			totalRevenue.append([key[:3].title(),float(inputDict.get(key, 0))])
	outData["monthlyNoConsumerServedSales"] = sorted(monthlyNoConsumerServedSales, key=lambda x:months[x[0]])
	outData["monthlyKWhSold"] = sorted(monthlyKWhSold, key=lambda x:months[x[0]])
	outData["monthlyRevenue"] = sorted(monthlyRevenue, key=lambda x:months[x[0]])
	outData["totalKWhSold"] = sorted(totalKWhSold, key=lambda x:months[x[0]])
	outData["totalRevenue"] = sorted(totalRevenue, key=lambda x:months[x[0]])
	outData["lossesBAU"] = float(inputDict.get("totalKWhPurchased", 0)) - sum([totalKWhSold[i][1] for i in range(12)]) 
	outData["lineLossRate"] = outData.get("lossesBAU", 0) / float(inputDict.get("totalKWhPurchased", 0))
	outData["totalGeneration"] = [[sorted(months.items(), key=lambda x:x[1])[i][0], outData["monthlyGeneration"][i][1]*monthlyNoConsumerServedSales[i][1]*float(inputDict.get("resPenetration", 0.05))/1000] for i in range(12)]
	##################
	# TODO: add retailCost to the calculation.
	##################
	## Flow Diagram Calculations, and order of calculation matters
	# BAU case
	outData["BAU"] = {}
	# E23 = E11
	outData["BAU"]["totalKWhPurchased"] = float(inputDict.get("totalKWhPurchased", 0))
	# E24 = SUM(E19:P19)
	outData["BAU"]["totalKWhSales"] = sum([monthlyKWhSold[i][1] for i in range(12)])
	# E25 = E23-E24
	outData["BAU"]["losses"] = outData["BAU"]["totalKWhPurchased"] - outData["BAU"]["totalKWhSales"]
	# E26 = E25/E23
	outData["BAU"]["effectiveLossRate"] = outData["BAU"]["losses"] / outData["BAU"]["totalKWhPurchased"]
	# E27 = 0
	outData["BAU"]["annualSolarGen"] = 0
	# E28 = SUM(E17:P17)
	outData["BAU"]["resNonSolarKWhSold"] = sum([monthlyKWhSold[i][1] for i in range(12)])
	# E29 = 0
	outData["BAU"]["solarResDemand"] = 0
	# E30 = 0
	outData["BAU"]["solarResSold"] = 0
	# E31 = E24-E28
	outData["BAU"]["nonResKWhSold"] = outData["BAU"]["totalKWhSales"] - outData["BAU"]["resNonSolarKWhSold"]
	# E32 = 0
	outData["BAU"]["costSolarGen"] = 0
	# E33 = SUM(E20:P20)-SUM(E18:P18)+E10
	outData["BAU"]["nonResRev"] = sum([totalRevenue[i][1] for i in range(12)]) - sum([monthlyRevenue[i][1] for i in range(12)]) + float(inputDict.get("otherElecRevenue"))
	# E34 = SUM(E18:P18)/SUM(E17:P17)
	outData["BAU"]["effectiveResRate"] = sum([monthlyRevenue[i][1] for i in range(12)])/sum([monthlyKWhSold[i][1] for i in range(12)])
	# E35 = E34*E28
	outData["BAU"]["resNonSolarRev"] = outData["BAU"]["effectiveResRate"] * outData["BAU"]["resNonSolarKWhSold"]
	# E36 = E30*E34
	outData["BAU"]["solarResRev"] = 0
	# E37 = SUM(E48:E54)+SUM(E56:E62)-SUM(E65:E71), update after Form 7 model
	outData["BAU"]["nonPowerCosts"] = 0 
	# E38 = E23-E25-E28-E30-E31
	outData["BAU"]["energyAllBal"] = 0
	# E39 = E36+E33+E35-E47-E72-E37
	outData["BAU"]["dollarAllBal"] = 0
	# E40 = 0
	outData["BAU"]["avgMonthlyBillSolarCus"] = 0
	# E41 = E6+E35/AVERAGE(D16:O16)/12
	outData["BAU"]["avgMonthlyBillNonSolarCus"] = float(inputDict.get("customServiceCharge", 0))+outData["BAU"]["resNonSolarRev"]/sum([monthlyNoConsumerServedSales[i][1] for i in range(12)])/12
	# E42 = E63/E24, update after Form 7 model
	outData["BAU"]["idealRate"] = 0
	# Solar case
	outData["Solar"] = {}
	# F27 = SUM(E15:P15)
	outData["Solar"]["annualSolarGen"] = sum([outData["totalGeneration"][i][1] for i in range(12)])
	# F24 = E24-F27
	outData["Solar"]["totalKWhSales"] = outData["BAU"]["totalKWhSales"] - outData["Solar"]["annualSolarGen"]
	# F23 =F24/(1-E26)
	outData["Solar"]["totalKWhPurchased"] = outData["Solar"]["totalKWhSales"]/(1-outData["BAU"]["effectiveLossRate"])
	# F25 = F23-F24
	outData["Solar"]["losses"] = outData["Solar"]["totalKWhPurchased"] - outData["Solar"]["totalKWhSales"]
	# F26 = E26
	outData["Solar"]["effectiveLossRate"] = outData["BAU"]["effectiveLossRate"]
	# F28 = (1-E5)*E28
	outData["Solar"]["resNonSolarKWhSold"] = (1-float(inputDict.get("residentialCustomWithSolarRate", 0.05)))*outData["BAU"]["resNonSolarKWhSold"]
	# F29 = E5*E28
	outData["Solar"]["solarResDemand"] = float(inputDict.get("residentialCustomWithSolarRate", 0.05))*outData["BAU"]["resNonSolarKWhSold"]
	# F30 = F29-F27
	outData["Solar"]["solarResSold"] = outData["Solar"]["solarResDemand"] - outData["Solar"]["annualSolarGen"]
	# F31 = E31
	outData["Solar"]["nonResKWhSold"] = outData["BAU"]["nonResKWhSold"]
	# F32 = E9*F27
	outData["Solar"]["costSolarGen"] = float(inputDict.get("solarLCoE", 0.07))*outData["Solar"]["annualSolarGen"]
	# F33 = E33
	outData["Solar"]["nonResRev"] = outData["BAU"]["nonResRev"]
	# F34 = E34
	outData["Solar"]["effectiveResRate"] = outData["BAU"]["effectiveResRate"]
	# F35 = F28*E34
	outData["Solar"]["resNonSolarRev"] = outData["Solar"]["effectiveResRate"] * outData["Solar"]["resNonSolarKWhSold"]
	# F36 = F30*E34
	outData["Solar"]["solarResRev"] = outData["Solar"]["solarResSold"] * outData["Solar"]["effectiveResRate"]
	# F37 = SUM(E48:E54)+SUM(E56:E62)-SUM(E65:E71) = E37, update after Form 7 model
	outData["Solar"]["nonPowerCosts"] = 0
	# F38 = F23-F25-F28-F30-E31
	outData["Solar"]["energyAllBal"] = 0
	# F39 = F36+E33+F35-F47-F72-E37
	outData["Solar"]["dollarAllBal"] = 0
	# F40 = E6+E7+(F36+F32)/E5/AVERAGE(E16:P16)/12
	outData["Solar"]["avgMonthlyBillSolarCus"] = float(inputDict.get("customServiceCharge", 0))+float(inputDict.get("solarInterconCharge", 0))+(outData["Solar"]["solarResRev"]+outData["Solar"]["costSolarGen"])/float(inputDict.get("residentialCustomWithSolarRate", 0.05))/sum([monthlyNoConsumerServedSales[i][1] for i in range(12)])/12/12
	# F41 = E6+F35/(1-E5)/AVERAGE(E16:P16)/12
	outData["Solar"]["avgMonthlyBillNonSolarCus"] = float(inputDict.get("customServiceCharge", 0)) + outData["Solar"]["resNonSolarRev"]/(1-float(inputDict.get("residentialCustomWithSolarRate", 0.05)))/sum(monthlyNoConsumerServedSales[i][1] for i in range(12))/12/12   +outData["Solar"]["resNonSolarRev"]/sum([monthlyNoConsumerServedSales[i][1] for i in range(12)])/12
	# F42 = F63/F24, update after Form 7 model
	outData["Solar"]["idealRate"] = 0

	## Form 7 Model
	# E46
	outData["Solar"]["powerProExpense"] = outData["BAU"]["powerProExpense"] = float(inputDict.get("powerProExpense", 0))
	# E47 != F47
	outData["BAU"]["costPurchasedPower"] = float(inputDict.get("costPurchasedPower", 0))
	# E48
	outData["Solar"]["transExpense"] = outData["BAU"]["transExpense"] = float(inputDict.get("transExpense", 0))
	# E49
	outData["Solar"]["distriExpenseO"] = outData["BAU"]["distriExpenseO"] = float(inputDict.get("distriExpenseO", 0))
	# E50
	outData["Solar"]["distriExpenseM"] = outData["BAU"]["distriExpenseM"] = float(inputDict.get("distriExpenseM", 0))
	# E51
	outData["Solar"]["customerAccountExpense"] = outData["BAU"]["customerAccountExpense"] = float(inputDict.get("customerAccountExpense", 0))
	# E52
	outData["Solar"]["customerServiceExpense"] = outData["BAU"]["customerServiceExpense"] = float(inputDict.get("customerServiceExpense", 0))
	# E53
	outData["Solar"]["salesExpense"] = outData["BAU"]["salesExpense"] = float(inputDict.get("salesExpense", 0))
	# E54
	outData["Solar"]["adminGeneralExpense"] = outData["BAU"]["adminGeneralExpense"] = float(inputDict.get("adminGeneralExpense", 0))
	# E56
	outData["Solar"]["depreAmortiExpense"] = outData["BAU"]["depreAmortiExpense"] = float(inputDict.get("depreAmortiExpense", 0))
	# E57
	outData["Solar"]["taxExpensePG"] = outData["BAU"]["taxExpensePG"] = float(inputDict.get("taxExpensePG", 0))
	# E58
	outData["Solar"]["taxExpense"] = outData["BAU"]["taxExpense"] = float(inputDict.get("taxExpense", 0))
	# E59
	outData["Solar"]["interestLongTerm"] = outData["BAU"]["interestLongTerm"] = float(inputDict.get("interestLongTerm", 0))
	# E60
	outData["Solar"]["interestConstruction"] = outData["BAU"]["interestConstruction"] = float(inputDict.get("interestConstruction", 0))
	# E61
	outData["Solar"]["interestExpense"] = outData["BAU"]["interestExpense"] = float(inputDict.get("interestExpense", 0))
	# E62
	outData["Solar"]["otherDeductions"] = outData["BAU"]["otherDeductions"] = float(inputDict.get("otherDeductions", 0))
	# E65
	outData["Solar"]["nonOpMarginInterest"] = outData["BAU"]["nonOpMarginInterest"] = float(inputDict.get("nonOpMarginInterest", 0))
	# E66
	outData["Solar"]["fundsUsedConstruc"] = outData["BAU"]["fundsUsedConstruc"] = float(inputDict.get("fundsUsedConstruc", 0))
	# E67
	outData["Solar"]["incomeEquityInvest"] = outData["BAU"]["incomeEquityInvest"] = float(inputDict.get("incomeEquityInvest", 0))
	# E68
	outData["Solar"]["nonOpMarginOther"] = outData["BAU"]["nonOpMarginOther"] = float(inputDict.get("nonOpMarginOther", 0))
	# E69
	outData["Solar"]["genTransCapCredits"] = outData["BAU"]["genTransCapCredits"] = float(inputDict.get("genTransCapCredits", 0))
	# E70
	outData["Solar"]["otherCapCreditsPatroDivident"] = outData["BAU"]["otherCapCreditsPatroDivident"] = float(inputDict.get("otherCapCreditsPatroDivident", 0))
	# E71
	outData["Solar"]["extraItems"] = outData["BAU"]["extraItems"] = float(inputDict.get("extraItems", 0))
	# Calculation
	# E45 = SUM(E20:P20)+E10
	outData["BAU"]["operRevPatroCap"] = sum([totalRevenue[i][1] for i in range(12)])+float(inputDict.get("otherElecRevenue", 0))
	# E55 = SUM(E46:E54)
	outData["BAU"]["totalOMExpense"] = float(inputDict.get("powerProExpense")) \
		+ float(inputDict.get("costPurchasedPower")) \
		+ float(inputDict.get("transExpense")) \
		+ float(inputDict.get("distriExpenseO")) \
		+ float(inputDict.get("distriExpenseM")) \
		+ float(inputDict.get("customerAccountExpense")) \
		+ float(inputDict.get("customerServiceExpense")) \
		+ float(inputDict.get("salesExpense"))  \
		+ float(inputDict.get("adminGeneralExpense"))
	# E63 = SUM(E55:E62)
	outData["BAU"]["totalCostElecService"] = outData["BAU"]["totalOMExpense"] \
		+ float(inputDict.get("depreAmortiExpense"))\
		+ float(inputDict.get("taxExpensePG"))\
		+ float(inputDict.get("taxExpense"))\
		+ float(inputDict.get("interestLongTerm"))\
		+ float(inputDict.get("interestExpense"))\
		+ float(inputDict.get("interestConstruction"))
	# E64 = E45-E63
	outData["BAU"]["patCapOperMargins"] = outData["BAU"]["operRevPatroCap"] - outData["BAU"]["totalCostElecService"]
	# E72 = SUM(E64:E71)
	outData["BAU"]["patCapital"] = outData["BAU"]["patCapOperMargins"]\
		+ float(inputDict.get("nonOpMarginInterest"))\
		+ float(inputDict.get("fundsUsedConstruc"))\
		+ float(inputDict.get("incomeEquityInvest"))\
		+ float(inputDict.get("nonOpMarginOther"))\
		+ float(inputDict.get("genTransCapCredits"))\
		+ float(inputDict.get("otherCapCreditsPatroDivident"))\
		+ float(inputDict.get("extraItems"))
	# F45 = E45-F27*E34
	outData["Solar"]["operRevPatroCap"] = outData["BAU"]["operRevPatroCap"] - outData["BAU"]["effectiveResRate"]*outData["Solar"]["annualSolarGen"]
	# F47 = (F23)*E8
	outData["Solar"]["costPurchasedPower"] = outData["Solar"]["totalKWhPurchased"] * float(inputDict.get("wholesaleEnergyCost", 0))
	# F55 = SUM(F46:F54)
	outData["Solar"]["totalOMExpense"] = outData["Solar"]["powerProExpense"]\
		+ outData["Solar"]["costPurchasedPower"]\
		+ outData["Solar"]["transExpense"]\
		+ outData["Solar"]["distriExpenseO"]\
		+ outData["Solar"]["distriExpenseM"]\
		+ outData["Solar"]["customerAccountExpense"]\
		+ outData["Solar"]["customerServiceExpense"]\
		+ outData["Solar"]["salesExpense"]\
		+ outData["Solar"]["adminGeneralExpense"]
	# F63 = E63
	outData["Solar"]["totalCostElecService"] = outData["Solar"]["totalOMExpense"]\
		+ outData["Solar"]["depreAmortiExpense"]\
		+ outData["Solar"]["taxExpensePG"]\
		+ outData["Solar"]["taxExpense"]\
		+ outData["Solar"]["interestLongTerm"]\
		+ outData["Solar"]["interestConstruction"]\
		+ outData["Solar"]["interestExpense"]\
		+ outData["Solar"]["otherDeductions"]
	# F64 = F45 - F63
	outData["Solar"]["patCapOperMargins"] = outData["Solar"]["operRevPatroCap"] - outData["Solar"]["totalCostElecService"]
	# F72 = SUM(F64:F71)
	outData["Solar"]["patCapital"] = outData["Solar"]["patCapOperMargins"]\
		+ outData["Solar"]["nonOpMarginInterest"]\
		+ outData["Solar"]["fundsUsedConstruc"]\
		+ outData["Solar"]["incomeEquityInvest"]\
		+ outData["Solar"]["nonOpMarginOther"]\
		+ outData["Solar"]["genTransCapCredits"]\
		+ outData["Solar"]["otherCapCreditsPatroDivident"]\
		+ outData["Solar"]["extraItems"]
	# E37 = SUM(E48:E54)+SUM(E56:E62)-SUM(E65:E71), update after Form 7 model
	outData["BAU"]["nonPowerCosts"] = outData["BAU"]["transExpense"] \
		+ outData["BAU"]["distriExpenseO"] \
		+ outData["BAU"]["distriExpenseM"] \
		+ outData["BAU"]["customerAccountExpense"] \
		+ outData["BAU"]["customerServiceExpense"] \
		+ outData["BAU"]["salesExpense"] \
		+ outData["BAU"]["adminGeneralExpense"] \
		+ outData["BAU"]["depreAmortiExpense"] \
		+ outData["BAU"]["taxExpensePG"] \
		+ outData["BAU"]["taxExpense"] \
		+ outData["BAU"]["interestLongTerm"] \
		+ outData["BAU"]["interestConstruction"] \
		+ outData["BAU"]["interestExpense"] \
		+ outData["BAU"]["otherDeductions"] \
		- (outData["BAU"]["nonOpMarginInterest"] \
		+ outData["BAU"]["fundsUsedConstruc"] \
		+ outData["BAU"]["incomeEquityInvest"] \
		+ outData["BAU"]["nonOpMarginOther"] \
		+ outData["BAU"]["genTransCapCredits"] \
		+ outData["BAU"]["otherCapCreditsPatroDivident"] \
		+ outData["BAU"]["extraItems"])
	# E42 = E63/E24, update after Form 7 model
	outData["BAU"]["idealRate"] = outData["BAU"]["totalCostElecService"] / outData["BAU"]["totalKWhSales"]
	# F37 = SUM(E48:E54)+SUM(E56:E62)-SUM(E65:E71) = E37, update after Form 7 model
	outData["Solar"]["nonPowerCosts"] = outData["BAU"]["nonPowerCosts"]
	# F42 = F63/F24, update after Form 7 model
	outData["Solar"]["idealRate"] = outData["Solar"]["totalCostElecService"] / outData["Solar"]["totalKWhSales"]
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	# Write the output.
	with open(pJoin(modelDir,"allOutputData.json"),"w") as outFile:
		json.dump(outData, outFile, indent=4)
	# Update the runTime in the input file.
	endTime = dt.datetime.now()
	inputDict["runTime"] = str(dt.timedelta(seconds=int((endTime - startTime).total_seconds())))
	with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
		json.dump(inputDict, inFile, indent=4)

def cancel(modelDir):
	''' solarRates runs so fast it's pointless to cancel a run. '''
	pass

def _tests():
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	# TODO: Fix inData because it's out of date.
	monthlyData = {
	"janSale": "46668", "janKWh": "64467874", "janRev": "8093137", "janKWhT": "85628959", "janRevT": "10464278", 
	"febSale": "46724", "febKWh": "66646882", "febRev": "8812203", "febKWhT": "89818661", "febRevT": "11508047", 
	"marSale": "46876", "marKWh": "62467031", "marRev": "8277498", "marKWhT": "84780954", "marRevT": "10874720", 
	"aprSale": "46858", "aprKWh": "49781827", "aprRev": "6664021", "aprKWhT": "70552865", "aprRevT": "9122130", 
	"maySale": "46919", "mayKWh": "41078029", "mayRev": "5567683", "mayKWhT": "63397699", "mayRevT": "8214078", 
	"junSale": "46977", "junKWh": "40835343", "junRev": "5528717", "junKWhT": "64781785", "junRevT": "8332117", 
	"julSale": "47013", "julKWh": "58018686", "julRev": "7585", "julKWhT": "86140915", "julRevT": "10793395", 
	"augSale": "47114", "augKWh": "67825037", "augRev": "8836269", "augKWhT": "98032727", "augRevT": "12219454", 
	"sepSale": "47140", "sepKWh": "59707578", "sepRev": "7809767", "sepKWhT": "88193645", "sepRevT": "11052318", 
	"octSale": "47088", "octKWh": "46451858", "octRev": "6146975", "octKWhT": "70425336", "octRevT": "8936767", 
	"novSale": "47173", "novKWh": "41668828", "novRev": "5551288", "novKWhT": "65008851", "novRevT": "8228072", 
	"decSale": "47081", "decKWh": "53354283", "decRev": "7014717", "decKWhT": "73335526", "decRevT": "9385203" }
	inData = {
		"modelType": "solarRates",
		"climateName": "AL-HUNTSVILLE",
		"runTime": "",
		# Single data point
		"avgSystemSize": "5",
		"resPenetration": "0.05",
		"customServiceCharge": "0",
		"solarInterconCharge": "0",
		"wholesaleEnergyCost": "0.08",
		"solarLCoE": "0.07",
		"otherElecRevenue": "1544165",
		"totalKWhPurchased": "999330657",
		# Form 7 data
		"powerProExpense": "0",
		"costPurchasedPower": "80466749",
		"transExpense": "15027",
		"distriExpenseO": "5294026",
		"distriExpenseM": "5535844",
		"customerAccountExpense": "4426441",
		"customerServiceExpense": "643418",
		"salesExpense": "127084",
		"adminGeneralExpense": "8264362",
		"depreAmortiExpense": "8975862",
		"taxExpensePG": "0",
		"taxExpense": "197924",
		"interestLongTerm": "10195988",
		"interestConstruction": "0",
		"interestExpense": "209969",
		"otherDeductions": "126640",
		"nonOpMarginInterest": "123401",
		"fundsUsedConstruc":"0",
		"incomeEquityInvest":"0",
		"nonOpMarginOther": "811043",
		"genTransCapCredits": "1015764",
		"otherCapCreditsPatroDivident": "1135379",
		"extraItems":"0" }
	for key in monthlyData:
		inData[key] = monthlyData[key]
	modelLoc = pJoin(workDir,"admin","Automated solarRates Testing")
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()