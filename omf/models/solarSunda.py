''' Calculate solar photovoltaic system output using our special financial model. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, math, datetime as dt
from numpy import npv, pmt, irr
from os.path import join as pJoin
from os import walk
from jinja2 import Template
import __metaModel__
from __metaModel__ import *
from random import random
import xlwt, traceback, csv
# OMF imports
sys.path.append(__metaModel__._omfDir)
import feeder
from solvers import nrelsam

# Our HTML template for the interface:
with open(pJoin(__metaModel__._myDir,"solarSunda.html"),"r") as tempFile:
	template = Template(tempFile.read())
	#only has A,  and V
	
def renderTemplate(template, modelDir="", absolutePaths=False, datastoreNames={}):
	return __metaModel__.renderTemplate(template, modelDir, absolutePaths, datastoreNames)

def run(modelDir, inputDict):
	''' Run the model in its directory. '''
	# Delete output file every run if it exists
	try:
		os.remove(pJoin(modelDir,"allOutputData.json"))	
	except Exception, e:
		pass
	try:
		# Check whether model exist or not
		if not os.path.isdir(modelDir):
			os.makedirs(modelDir)
			inputDict["created"] = str(dt.datetime.now())
		# MAYBEFIX: remove this data dump. Check showModel in web.py and renderTemplate()
		with open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(inputDict, inputFile, indent = 4)
		#Set static input data
		inputDict["simLength"] = "8760"
		inputDict["simStartDate"] = "2013-01-01"
		inputDict["simLengthUnits"] = "hours"
		inputDict["modelType"] = "solarSunda"
		# Associate zipcode to climate data
		try: 
			if inputDict["test"] == "True":
				inputDict["climateName"] = zipCodeToclimateName(inputDict["zipCode"], test="True")	
		except:
			inputDict["climateName"] = zipCodeToclimateName(inputDict["zipCode"], test="False")	
		inputDict["panelSize"] = 305   
		arraySizeAC = float(inputDict.get("systemSize",0))
		arraySizeDC = arraySizeAC*1.3908
		numberPanels = (arraySizeDC*1000/305)		
		inputDict["derate"] = "87"		
		inputDict["inverterEfficiency"] = "96"
		#Use latitude for tilt	
		inputDict["tilt"] = "True"	
		inputDict["manualTilt"] = "39"		
		inputDict["trackingMode"] = "0"
		inputDict["azimuth"] = "180"		
		inputDict["runTime"] = ""				
		inputDict["rotlim"] = "45.0"
		inputDict["gamma"] = "-0.45"
		inputDict["omCost"] = "1000"	
		if (float(inputDict["systemSize"]) > 250):
			inputDict["inverterCost"] = float(107000)
		else:
			inputDict["inverterCost"] = float(61963)			
		numberInverters = math.ceil(arraySizeAC/1000/0.5)
		minLandSize = arraySizeAC/1000*5 + 1		
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
		ssc.ssc_data_set_number(dat, "system_size", float(inputDict.get("systemSize", 100)))
		derate = float(inputDict.get("derate", 100))/100 * float(inputDict.get("inverterEfficiency", 92))/100
		ssc.ssc_data_set_number(dat, "derate", derate)
		ssc.ssc_data_set_number(dat, "track_mode", float(inputDict.get("trackingMode", 0)))
		ssc.ssc_data_set_number(dat, "azimuth", float(inputDict.get("azimuth", 180)))
		# Advanced inputs with defaults.
		ssc.ssc_data_set_number(dat, "rotlim", float(inputDict.get("rotlim", 45)))
		ssc.ssc_data_set_number(dat, "gamma", float(inputDict.get("gamma", 0.5))/100)
		# Complicated optional inputs.
		ssc.ssc_data_set_number(dat, "tilt_eq_lat", 1) 
		#must be true to have tilt set to tilt value, but tilt isnt provided to pvwatts?
		# Run PV system simulation.
		mod = ssc.ssc_module_create("pvwattsv1")
		ssc.ssc_module_exec(mod, dat)
		# Setting options for start time.
		simLengthUnits = inputDict.get("simLengthUnits","hours")
		simStartDate = inputDict.get("simStartDate", "2014-01-01")
		# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html 
		startDateTime = simStartDate + " 00:00:00 UTC"
		# Timestamp output.
		outData = {}
		outData["timeStamps"] = [dt.datetime.strftime(
			dt.datetime.strptime(startDateTime[0:19],"%Y-%m-%d %H:%M:%S") + 
			dt.timedelta(**{simLengthUnits:x}),"%Y-%m-%d %H:%M:%S") + " UTC" for x in range(int(inputDict.get("simLength", 8760)))]
		# Geodata output.
		outData["city"] = ssc.ssc_data_get_string(dat, "city")
		outData["state"] = ssc.ssc_data_get_string(dat, "state")
		outData["lat"] = ssc.ssc_data_get_number(dat, "lat")
		outData["lon"] = ssc.ssc_data_get_number(dat, "lon")
		outData["elev"] = ssc.ssc_data_get_number(dat, "elev")
		# Weather output.
		outData["climate"] = {}
		outData["climate"]["Global Horizontal Radiation (W/m^2)"] = ssc.ssc_data_get_array(dat, "gh")
		outData["climate"]["Plane of Array Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "poa")
		outData["climate"]["Ambient Temperature (F)"] = ssc.ssc_data_get_array(dat, "tamb")
		outData["climate"]["Cell Temperature (F)"] = ssc.ssc_data_get_array(dat, "tcell")
		outData["climate"]["Wind Speed (m/s)"] = ssc.ssc_data_get_array(dat, "wspd")		
		# Power generation.
		outData["powerOutputAc"] = ssc.ssc_data_get_array(dat, "ac")	
		#One year generation	
		outData["oneYearGenerationWh"] = sum(outData["powerOutputAc"]) 
		#Annual generation for all years
		loanYears = 25		
		outData["allYearGenerationMWh"] = {}		
		outData["allYearGenerationMWh"][1] = float(outData["oneYearGenerationWh"])/1000000
		for i in range (2, loanYears+1):
			outData["allYearGenerationMWh"][i] = float(outData["allYearGenerationMWh"][i-1])*0.992


		# Summary of Results.
		'''Total Costs including: Hardware, design/labor, siteprep, construction, install, and land'''
		'''Hardware Costs: '''
		pvModules = arraySizeDC * float(inputDict.get("moduleCost",0))*1000 #off by 4000
		racking = arraySizeDC * float(inputDict.get("rackCost",0))*1000
		inverters = numberInverters * float(inputDict.get("inverterCost",0))
		inverterSize = arraySizeAC
		if (inverterSize <= 250): 
			gear = 15000		
		elif (inverterSize <= 600):
			gear = 18000
		else:
			gear = inverterSize/1000 * 22000
		balance = arraySizeAC*1.3908 * 134
		combiners = math.ceil(numberPanels/19/24) * float(1800)  #*
		wireManagement = arraySizeDC*1.5
		transformer = 1 * 28000
		weatherStation = 1 * 12500
		shipping = 1.02
		includeModules = 1
		if (includeModules == 1):
			hardwareCosts = (pvModules + racking + inverters + gear + balance + combiners + wireManagement  + transformer + weatherStation) * shipping
		else:
			hardwareCosts = (racking + inverters + gear + balance + combiners + wireManagement  + transformer + weatherStation) * shipping + pvModules	

		'''Design/Engineering/PM/EPC costs: (called labor costs)'''	
		EPCmarkup = float(inputDict.get("EPCRate",0))/100 * hardwareCosts
		#designCosts = float(inputDict.get("mechLabor",0))*160 + float(inputDict.get("elecLabor",0))*75 + float(inputDict.get("pmCost",0)) + EPCmarkup	
		hoursDesign = 160*math.sqrt(arraySizeDC/1390)
		hoursElectrical = 80*math.sqrt(arraySizeDC/1391)
		designLabor = 65*hoursDesign
		electricalLabor = 75*hoursElectrical
		laborDesign = designLabor + electricalLabor + float(inputDict.get("pmCost",0)) + EPCmarkup
		materialDesign = 0
		designCosts = materialDesign + laborDesign

		'''Siteprep Costs:'''
		surveying = 2.25 * 4 * math.sqrt(minLandSize*43560)
		concrete = 8000 * math.ceil(numberInverters/2)
		fencing = 6.75 * 4 * math.sqrt(minLandSize*43560)
		grading = 2.5 * 4 * math.sqrt(minLandSize*43560)
		landscaping = 750 * minLandSize
		siteMaterial = 8000 + 600 + 5500 + 5000 + surveying + concrete + fencing + grading + landscaping + 5600
		blueprints = float(inputDict.get("mechLabor",0))*12 
		mobilization = float(inputDict.get("mechLabor",0))*208
		mobilizationMaterial = float(inputDict.get("mechLabor",0))*19.98
		siteLabor = blueprints + mobilization + mobilizationMaterial
		sitePrep = siteMaterial + siteLabor

		'''Construction equipment Costs: Office Trailer, Skid Steer, Storage Containers, etc
		'''		
		constrEquip = 6000 + math.sqrt(minLandSize)*16200

		'''Installation Costs:'''
		moduleAndRackingInstall = numberPanels * (15.00 + 12.50 + 1.50) 
		pierDriving = 1 * arraySizeDC*20
		balanceInstall = 1 * arraySizeDC*100
		installCosts = moduleAndRackingInstall + pierDriving + balanceInstall + float(inputDict.get("elecLabor",0)) * (72 + 60 + 70 + 10 + 5 + 30 + 70)

		'''Land Costs:'''
		if (str(inputDict.get("landOwnership",0)) == "Owned" or (str(inputDict.get("landOwnership",0)) == "Leased")):
			landCosts = 0
		else:
			landCosts = float(inputDict.get("costAcre",0))*minLandSize

		'''Total costs (Sum of all above): '''
		totalCosts = hardwareCosts + designCosts + sitePrep + constrEquip + installCosts + landCosts
		totalFees= float(inputDict.get("devCost",0))/100 * totalCosts
		outData["totalCost"] = totalCosts + totalFees + float(inputDict.get("interCost",0))
		# Cost per Wdc
		outData["costWdc"] = totalCosts / (arraySizeAC * 1000 * 1.39)

		outData["capFactor"] = float(outData["oneYearGenerationWh"])/(arraySizeAC*1000*365.25*24) * 100

		'''Loans calculations for Direct, NCREB, Lease, Tax-equity, and PPA'''
		'''Full Ownership, Direct Loan'''
		#Output - Direct Loan [C]
		projectCostsDirect = 0		
		#Output - Direct Loan [D]	
		netFinancingCostsDirect = 0	
		#Output - Direct Loan [E]	
		OMInsuranceETCDirect = []	
		#Output - Direct Loan [F]	
		distAdderDirect = []	
		#Output - Direct Loan [G]				
		netCoopPaymentsDirect = []	
		#Output - Direct Loan [H]			
		costToCustomerDirect = []			
		#Output - Direct Loan [F53]
		Rate_Levelized_Direct = 0

		#Output - Direct Loan Formulas
		projectCostsDirect = 0
		#Output - Direct Loan [D]						
		payment = pmt(float(inputDict.get("loanRate",0))/100, loanYears, outData["totalCost"])
		interestDirectPI = outData["totalCost"] * float(inputDict.get("loanRate",0))/100
		principleDirectPI = (-payment - interestDirectPI)
		patronageCapitalRetiredDPI = 0
		netFinancingCostsDirect = -(principleDirectPI + interestDirectPI - patronageCapitalRetiredDPI)
		'''
		interestDirect = outData["totalCost"] * float(inputDict.get("loanRate",0))/100
		payment = pmt(float(inputDict.get("loanRate",0))/100, loanYears, outData["totalCost"]) #determine initial payment		
		principleDirect =  (-payment - interestDirect)
		netFinancingCostsDirect = principleDirect + interestDirect - patronageCapitalRetired
		'''

		#Output - Direct Loan [E] [F] [G] [H]
		firstYearOPMainCosts = (1.25 * arraySizeDC * 12) 
		firstYearInsuranceCosts = (0.37 * outData["totalCost"]/100) 
		if (inputDict.get("landOwnership",0) == "Leased"):
			firstYearLandLeaseCosts = float(inputDict.get("costAcre",0))*minLandSize
		else:
			firstYearLandLeaseCosts = 0					
		for i in range (1, len(outData["allYearGenerationMWh"])+1):	
			OMInsuranceETCDirect.append(-firstYearOPMainCosts*math.pow((1 + .01),(i-1)) - firstYearInsuranceCosts*math.pow((1 + .025),(i-1)) - firstYearLandLeaseCosts*math.pow((1 + .01),(i-1)))	
			distAdderDirect.append(float(inputDict.get("distAdder",0))*outData["allYearGenerationMWh"][i])				
			netCoopPaymentsDirect.append(OMInsuranceETCDirect[i-1] + netFinancingCostsDirect)
			costToCustomerDirect.append((netCoopPaymentsDirect[i-1] - distAdderDirect[i-1]))
		#NPVLoanDirect = npv(float(inputDict.get("discRate",0))/100,costToCustomerDirect) #Wrong result with numpy.npv
		NPVLoanDirect = 0
		for i in range (1, len(outData["allYearGenerationMWh"])+1):
			NPVLoanDirect = NPVLoanDirect + costToCustomerDirect[i-1]/(math.pow(1+0.0232,i))	

		#Output - Direct Loan [F53]
		revLevelizedCost = []
		NPVRevDirect = 0
		x = 3500
		Rate_Levelized_Direct = x/100.0
		nGoal = - NPVLoanDirect	
		nValue = NPVRevDirect	
		#First Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevDirect = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_Direct*outData["allYearGenerationMWh"][i])
				NPVRevDirect = NPVRevDirect + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevDirect				
			x = x + 100.0		
			Rate_Levelized_Direct = x/100.0					
		while ((x > 2500) and (nValue > nGoal)):
			NPVRevDirect = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_Direct*outData["allYearGenerationMWh"][i])
				NPVRevDirect = NPVRevDirect + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevDirect				
			x = x - 10.0		
			Rate_Levelized_Direct = x/100.0						
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevDirect = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_Direct*outData["allYearGenerationMWh"][i])
				NPVRevDirect = NPVRevDirect + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevDirect				
			x = x + 1.0			
			Rate_Levelized_Direct = x/100.0							

		#Master Output [Direct Loan]
		outData["levelCostDirect"] = Rate_Levelized_Direct
		outData["costPanelDirect"] = abs(NPVLoanDirect/numberPanels)
		outData["cost10WPanelDirect"] = (float(outData["costPanelDirect"])/inputDict["panelSize"])*10


		'''NCREBs Financing'''
		#Output - NCREBs [C]
		projectCostsNCREB = 0
		#Output - NCREBs [D]
		netFinancingCostsNCREB = []
		#Output - NCREBs [E]
		OMInsuranceETCNCREB = OMInsuranceETCDirect
		#Output - NCREBs [F]
		distAdderNCREB = distAdderDirect
		#Output - NCREBs [G]
		netCoopPaymentsNCREB = []
		#Output - NCREBs [H]
		costToCustomerNCREB = []
		#Output - NCREBs [H44]
		NPVLoanNCREB = 0
		#Output - NCREBs [F48]
		Rate_Levelized_NCREB = 0


		#NCREBs Formulas
		#Output - NCREBs [D]
		#NCREBS P&I [C7]
		loanYearsNCREB = 52
		#NCREBS P&I [C9]
		payment = pmt(1.1*float(inputDict.get("NCREBRate",0))/100/2, loanYearsNCREB, -outData["totalCost"])	
        #NCREBs P&I [C]
        #levelDebtServiceNCREBPI = 0
        #NCREBs P&I [D]
		princPaymentNCREBPI = []
		#NCREBs P&I [E]
		interestPaymentNCREBPI = []
		#NCREBs P&I [F]
		balanceOutstandingNCREBPI = []
		#NCREBs P&I [I]
		percentofTaxCreditNCREBPI = []
		#NCREBs P&I [K]		
		netInterestNCREBPI = []		
		#NCREBs P&I [M]		
		cashflowNCREBPI = []
		balanceOutstandingNCREBPI.append(outData["totalCost"])
		interestPaymentNCREBPI.append(round(float(balanceOutstandingNCREBPI[0])*1.1*float(inputDict.get("NCREBRate",0))/100/2,2))
		for i in range (0, loanYearsNCREB):
			if (payment - float(interestPaymentNCREBPI[i]) > float(balanceOutstandingNCREBPI[i])):
				princPaymentNCREBPI.append(float(balanceOutstandingNCREBPI[i]))
			else:
				princPaymentNCREBPI.append(payment - float(interestPaymentNCREBPI[i]))
			balanceOutstandingNCREBPI.append(float(balanceOutstandingNCREBPI[i]) - float(princPaymentNCREBPI[i]))
			if (i+1 >= 43):
				percentofTaxCreditNCREBPI.append(round(float(balanceOutstandingNCREBPI[i])*.03213/2,2))	
			else:
				percentofTaxCreditNCREBPI.append(round(float(balanceOutstandingNCREBPI[i])*0.7*float(inputDict.get("NCREBRate",0))/100/2,2))			
			if (i+1 >= 50):
				interestPaymentNCREBPI.append(round(float(balanceOutstandingNCREBPI[i+1])*1.1*float(inputDict.get("NCREBRate",0))/100/4,2))
				netInterestNCREBPI.append(float(interestPaymentNCREBPI[i]) - float(percentofTaxCreditNCREBPI[i]))
				cashflowNCREBPI.append(float(princPaymentNCREBPI[i]) + float(netInterestNCREBPI[i]))					
			else:
				interestPaymentNCREBPI.append(round(float(balanceOutstandingNCREBPI[i+1])*1.1*float(inputDict.get("NCREBRate",0))/100/2,2))	
				netInterestNCREBPI.append(float(interestPaymentNCREBPI[i]) - float(percentofTaxCreditNCREBPI[i]))
				cashflowNCREBPI.append(float(princPaymentNCREBPI[i]) + float(netInterestNCREBPI[i]))
			if (i % 2):
				netFinancingCostsNCREB.append(float(cashflowNCREBPI[i-1]) + float(cashflowNCREBPI[i]))			
		levelDebtServiceNCREBPI = princPaymentNCREBPI[0] + interestPaymentNCREBPI[0]

		#Output - NCREBs [G] [H] - Total Net Coop Payments & Cost to Customer			
		for i in range (1, len(outData["allYearGenerationMWh"])+1):				
			netCoopPaymentsNCREB.append(float(OMInsuranceETCNCREB[i-1]) - float(netFinancingCostsNCREB[i-1]))
			costToCustomerNCREB.append((float(netCoopPaymentsNCREB[i-1]) - float(distAdderNCREB[i-1])))
		netCoopPaymentsNCREB.append(-float(netFinancingCostsNCREB[i]))
		costToCustomerNCREB.append(float(netCoopPaymentsNCREB[i]))

		#Output - NCREBs [H44]
		for i in range (1, len(costToCustomerNCREB)+1):
			NPVLoanNCREB = NPVLoanNCREB + costToCustomerNCREB[i-1]/(math.pow(1+0.0232,i))

		#Output - NCREBs [F48]
		revLevelizedCost = []
		NPVRevNCREB = 0
		x = 3500
		Rate_Levelized_NCREB = x/100.0
		nGoal = - NPVLoanNCREB	
		nValue = NPVRevNCREB
		#First Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevNCREB = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_NCREB*outData["allYearGenerationMWh"][i])
				NPVRevNCREB = NPVRevNCREB + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevNCREB				
			x = x + 100.0		
			Rate_Levelized_NCREB = x/100.0					
		#Second Loop
		while ((x > 2500) and (nValue > nGoal)):
			NPVRevNCREB = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_NCREB*outData["allYearGenerationMWh"][i])
				NPVRevNCREB = NPVRevNCREB + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevNCREB				
			x = x - 10.0		
			Rate_Levelized_NCREB = x/100.0						
		#Third Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevNCREB = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_NCREB*outData["allYearGenerationMWh"][i])
				NPVRevNCREB = NPVRevNCREB + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevNCREB				
			x = x + 1.0		
			Rate_Levelized_NCREB = x/100.0					

		#Master Output [NCREB]
		outData["levelCostNCREB"] = Rate_Levelized_NCREB	
		outData["costPanelNCREB"] = abs(NPVLoanNCREB/numberPanels)
		outData["cost10WPanelNCREB"] = (float(outData["costPanelNCREB"])/inputDict["panelSize"])*10

		'''Tax Lease Structure'''
		#Output - Lease [C]
		projectCostsLease = outData["totalCost"]
		#Output - Lease [D]
		leasePaymentsLease = []
		#Output - Lease [E]
		OMInsuranceETCLease = []
		#Output - Lease [F]
		distAdderLease = distAdderDirect
		#Output - Lease [G]
		netCoopPaymentsLease = []
		#Output - Lease [H]
		costToCustomerLease = []
		#Output - Lease [H44]
		NPVLease = 0
		#Output - Lease [H49]
		Rate_Levelized_Lease = 0

		#Tax Lease Formulas
		#Output - Lease [D]		
		monthlyLeaseFactorLease = float(inputDict.get("taxLeaseRate",0))/12
		for i in range (0, 11):
			leasePaymentsLease.append(-monthlyLeaseFactorLease/100*projectCostsLease*12)
		leasePaymentsLease.append(-0.2*projectCostsLease)
		for i in range (12, 25):		
			leasePaymentsLease.append(0)
	
		#Output - Lease [E]		
		OMInsuranceETCLease.append(OMInsuranceETCDirect[0])
		OMInsuranceETCLease.append(-30378)
		OMInsuranceETCLease.append(-30819)
		OMInsuranceETCLease.append(-31268)				
		OMInsuranceETCLease.append(-31725)
		OMInsuranceETCLease.append(-32191)
		OMInsuranceETCLease.append(-32664)	
		OMInsuranceETCLease.append(-33147)
		OMInsuranceETCLease.append(-33638)
		OMInsuranceETCLease.append(-34137)	
		OMInsuranceETCLease.append(-34646)
		OMInsuranceETCLease.append(-35165)
		OMInsuranceETCLease.append(-35692)	
		OMInsuranceETCLease.append(-36230)
		OMInsuranceETCLease.append(-36777)
		OMInsuranceETCLease.append(-37334)	
		OMInsuranceETCLease.append(-37902)
		OMInsuranceETCLease.append(-38480)
		OMInsuranceETCLease.append(-39069)	
		OMInsuranceETCLease.append(-39669)
		OMInsuranceETCLease.append(-40280)
		OMInsuranceETCLease.append(-40903)	
		OMInsuranceETCLease.append(-41537)
		OMInsuranceETCLease.append(-42183)
		OMInsuranceETCLease.append(-42842)

		#Output - Lease [G]	[H]	
		costToCustomerLeaseSum = 0	
		for i in range (1, len(outData["allYearGenerationMWh"])+1):
			netCoopPaymentsLease.append(OMInsuranceETCLease[i-1]+leasePaymentsLease[i-1])
			costToCustomerLease.append(netCoopPaymentsLease[i-1]-distAdderLease[i-1])
			costToCustomerLeaseSum = costToCustomerLeaseSum + costToCustomerLease[i-1]

		#Output - Lease [H44]
		NPVLease = costToCustomerLeaseSum/(math.pow(1+float(inputDict.get("discRate", 0))/100,1))		

		#Output - Lease [H49] 
		revLevelizedCost = []
		NPVRevLease = 0
		x = 3500
		Rate_Levelized_Lease = x/100.0
		nGoal = - NPVLease	
		nValue = NPVRevLease
		#First Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevLease = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_Lease*outData["allYearGenerationMWh"][i])
				NPVRevLease = NPVRevLease + revLevelizedCost[i-1]	
			nValue = NPVRevLease				
			x = x + 100.0		
			Rate_Levelized_Lease = x/100.0						
		#Second Loop
		while ((x > 2500) and (nValue > nGoal)):
			NPVRevLease = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_Lease*outData["allYearGenerationMWh"][i])
				NPVRevLease = NPVRevLease + revLevelizedCost[i-1]
			nValue = NPVRevLease				
			x = x - 10.0		
			Rate_Levelized_Lease = x/100.0						
		#Third Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevLease = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_Lease*outData["allYearGenerationMWh"][i])
				NPVRevLease = NPVRevLease + revLevelizedCost[i-1]	
			nValue = NPVRevLease				
			x = x + 1.0		
			Rate_Levelized_Lease = x/100.0					
			
		#Master Output [Lease]
		outData["levelCostTaxLease"] = Rate_Levelized_Lease	
		outData["costPanelTaxLease"] = abs(NPVLease/numberPanels)
		outData["cost10WPanelTaxLease"] = (float(outData["costPanelTaxLease"])/float(inputDict["panelSize"]))*10


		'''Tax Equity Flip Structure'''		
		z = 6791 
		PPARateSixYearsTE = z/100		
		nGoal = float(inputDict.get("taxEquityReturn",0))/100
		nValue = 0		
		#First Loop		
		while ((z < 20000) and (nValue < nGoal)):	
			IRRReturn = taxEquityFlip(PPARateSixYearsTE, inputDict, outData, distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels)
			#TEI Calcs - PPA [C]
			achievedReturnTE = IRRReturn
			nValue = achievedReturnTE
			z = z + 1000
			PPARateSixYearsTE = z/100.0
			#Loop back until nValue > nGoal (or Achieved Rate > Desired Rate)	
		#Second Loop		
		while ((z > 2500) and (nValue > nGoal)):	
			IRRReturn = taxEquityFlip(PPARateSixYearsTE, inputDict, outData, distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels)
			#TEI Calcs - PPA [C]
			achievedReturnTE = IRRReturn
			nValue = achievedReturnTE
			z = z - 100
			PPARateSixYearsTE = z/100.0			
		#Third Loop		
		while ((z < 20000) and (nValue < nGoal)):	
			IRRReturn = taxEquityFlip(PPARateSixYearsTE, inputDict, outData, distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels)
			#TEI Calcs - PPA [C]
			achievedReturnTE = IRRReturn
			nValue = achievedReturnTE
			z = z + 10
			PPARateSixYearsTE = z/100.0					
		#Fourth Loop		
		while ((z > 2500) and (nValue > nGoal)):	
			IRRReturn = taxEquityFlip(PPARateSixYearsTE, inputDict, outData, distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels)
			#TEI Calcs - PPA [C]
			achievedReturnTE = IRRReturn
			nValue = achievedReturnTE
			z = z - 1
			PPARateSixYearsTE = z/100.0


		'''PPA Comparison'''
		#Output - PPA [F]
		distAdderPPA = distAdderDirect
		#Output - PPA [G]
		netCoopPaymentsPPA = []
		#Output - PPA [H]
		costToCustomerPPA = []
		#Output - PPA [I]
		costToCustomerPPA = []		
		#Output - PPA [H40]
		NPVLoanPPA = 0
		#Output - PPA [I40]
		Rate_Levelized_PPA = 0

		#PPA Formulas
		#Output - PPA [G] [H]
		for i in range (1, len(outData["allYearGenerationMWh"])+1):
			netCoopPaymentsPPA.append(-outData["allYearGenerationMWh"][i]*float(inputDict.get("firstYearEnergyCostPPA",0))*math.pow((1 + float(inputDict.get("annualEscRatePPA", 0))/100),(i-1)))
			costToCustomerPPA.append(netCoopPaymentsPPA[i-1]-distAdderPPA[i-1])

		#Output - PPA [H40]
		for i in range (1, len(outData["allYearGenerationMWh"])+1):		
			NPVLoanPPA = NPVLoanPPA + costToCustomerPPA[i-1]/(math.pow(1+0.0232,i))

		#Output - PPA [F44] [I40] 
		revLevelizedCost = []
		NPVRevPPA = 0
		x = 3500
		Rate_Levelized_PPA = x/100.0
		nGoal = - NPVLoanPPA	
		nValue = NPVRevPPA
		#First Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevPPA = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_PPA*outData["allYearGenerationMWh"][i])
				NPVRevPPA = NPVRevPPA + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevPPA				
			x = x + 100.0		
			Rate_Levelized_PPA = x/100.0							
		#Second Loop		
		while ((x > 2500) and (nValue > nGoal)):
			NPVRevPPA = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_PPA*outData["allYearGenerationMWh"][i])
				NPVRevPPA = NPVRevPPA + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))	
			nValue = NPVRevPPA				
			x = x - 10.0		
			Rate_Levelized_PPA = x/100.0						
		#Third Loop		
		while ((x < 20000) and (nValue < nGoal)):
			NPVRevPPA = 0
			revLevelizedCost = []			
			for i in range (1, len(outData["allYearGenerationMWh"])+1):		
				revLevelizedCost.append(Rate_Levelized_PPA*outData["allYearGenerationMWh"][i])
				NPVRevPPA = NPVRevPPA + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
			nValue = NPVRevPPA				
			x = x + 1.0		
			Rate_Levelized_PPA = x/100.0						

		#Master PPA [Lease]
		outData["levelCostPPA"] = Rate_Levelized_PPA
		outData["firstYearCostKWhPPA"] = float(inputDict.get("firstYearEnergyCostPPA",0))
		outData["yearlyEscalationPPA"] = float(inputDict.get("annualEscRatePPA", 0))


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
	except:
		# If input range wasn't valid delete output, write error to disk.
		thisErr = traceback.format_exc()
		inputDict['stderr'] = thisErr
		with open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
		with open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
			json.dump(inputDict, inFile, indent=4)
		try:
			os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception, e:
			pass

#Tax Equity Flip Structure
def taxEquityFlip(PPARateSixYearsTE, inputDict, outData, distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels):
	#Output Tax Equity Flip [C]
	coopInvestmentTaxEquity = -float(outData["totalCost"])*(1-0.53)
	#Output Tax Equity Flip [D]
	financeCostCashTaxEquity = 0
	#Output Tax Equity Flip [E]
	cashToSPEOForPPATE  = []	
	#Output Tax Equity Flip [F]
	derivedCostEnergyTE  = 0	
	#Output Tax Equity Flip [G]
	OMInsuranceETCTE = []
	#Output Tax Equity Flip [H]
	cashFromSPEToBlockerTE = []
	#Output Tax Equity Flip [I]
	cashFromBlockerTE = 0
	#Output Tax Equity Flip [J]
	distAdderTaxEquity = distAdderDirect
	#Output Tax Equity Flip [K]
	netCoopPaymentsTaxEquity = []
	#Output Tax Equity Flip [L]
	costToCustomerTaxEquity = []		
	#Output Tax Equity Flip [L37]
	NPVLoanTaxEquity = 0
	#Output Tax Equity Flip [F42]
	Rate_Levelized_Equity = 0

	'''Tax Equity Flip Formulas'''
	#Output Tax Equity Flip [D]
	#TEI Calcs [E]
	financeCostOfCashTE = 0
	coopFinanceRateTE = 4.2/100
	if (coopFinanceRateTE == 0):
		financeCostOfCashTE = 0		
	else:
		payment = pmt(coopFinanceRateTE, loanYears, -coopInvestmentTaxEquity)
	financeCostCashTaxEquity = payment

	#Output Tax Equity Flip [E]
	SPERevenueTE = []
	for i in range (1, len(outData["allYearGenerationMWh"])+1):
		SPERevenueTE.append(PPARateSixYearsTE * outData["allYearGenerationMWh"][i])
		if ((i>=1) and (i<=6)):
			cashToSPEOForPPATE.append(-SPERevenueTE[i-1])
		else: 
			cashToSPEOForPPATE.append(0)

	#Output Tax Equity Flip [F]
	derivedCostEnergyTE = cashToSPEOForPPATE[0]/outData["allYearGenerationMWh"][1]

	#Output Tax Equity Flip [G]
	#TEI Calcs [F]	[U] [V]
	landLeaseTE = []
	OMTE = []
	insuranceTE = []		
	for i in range (1, len(outData["allYearGenerationMWh"])+1):	
		landLeaseTE.append(firstYearLandLeaseCosts*math.pow((1 + .01),(i-1)))				
		OMTE.append(-firstYearOPMainCosts*math.pow((1 + .01),(i-1)))	
		insuranceTE.append(- firstYearInsuranceCosts*math.pow((1 + .025),(i-1)) )	
		if (i<7):
			OMInsuranceETCTE.append(float(landLeaseTE[i-1]))
		else:
			OMInsuranceETCTE.append(float(OMTE[i-1]) + float(insuranceTE[i-1]) + float(landLeaseTE[i-1]))					
	#Output Tax Equity Flip [H]
	#TEI Calcs [T]	
	SPEMgmtFeeTE = []
	EBITDATE = []
	EBITDATEREDUCED = []
	managementFee = 10000
	for i in range (1, len(SPERevenueTE)+1):
		SPEMgmtFeeTE.append(-managementFee*math.pow((1 + .01),(i-1)))
		EBITDATE.append(float(SPERevenueTE[i-1]) + float(OMTE[i-1]) + float(insuranceTE[i-1]) + float(SPEMgmtFeeTE[i-1])) 
		if (i<=6):
			cashFromSPEToBlockerTE.append(float(EBITDATE[i-1]) * .01)
		else:
			cashFromSPEToBlockerTE.append(0)
			EBITDATEREDUCED.append(EBITDATE[i-1])


	#Output Tax Equity Flip [I]
	#TEI Calcs [Y21]			
	cashRevenueTE = -outData["totalCost"] * (1 - 0.53)
	buyoutAmountTE = 0
	for i in range (1, len(EBITDATEREDUCED) + 1):
		buyoutAmountTE = buyoutAmountTE + EBITDATEREDUCED[i-1]/(math.pow(1+0.12,i))
	buyoutAmountTE = buyoutAmountTE * 0.05
	cashFromBlockerTE = - (buyoutAmountTE) + 0.0725 * cashRevenueTE


	#Output Tax Equity Flip [K] [L]
	for i in range (1, len(outData["allYearGenerationMWh"])+1):	
		if (i==6):
			netCoopPaymentsTaxEquity.append(financeCostCashTaxEquity + cashToSPEOForPPATE[i-1] + cashFromSPEToBlockerTE[i-1] + OMInsuranceETCTE[i-1] + cashFromBlockerTE)	
		else:
			netCoopPaymentsTaxEquity.append(financeCostCashTaxEquity + cashFromSPEToBlockerTE[i-1] + cashToSPEOForPPATE[i-1] + OMInsuranceETCTE[i-1])
		costToCustomerTaxEquity.append(netCoopPaymentsTaxEquity[i-1] - distAdderTaxEquity[i-1])


	#Output Tax Equity Flip [L37]
	for i in range (1, len(costToCustomerTaxEquity) + 1):
		NPVLoanTaxEquity = NPVLoanTaxEquity + costToCustomerTaxEquity[i-1]/(math.pow(1+float(inputDict.get("discRate", 0))/100,i))

	#Output - Tax Equity [F42] 
	revLevelizedCost = []
	NPVRevTaxEquity = 0
	x = 3500
	Rate_Levelized_TaxEquity = x/100.0
	nGoal = - NPVLoanTaxEquity	
	nValue = NPVRevTaxEquity
	#First Loop		
	while ((x < 20000) and (nValue < nGoal)):
		NPVRevTaxEquity = 0
		revLevelizedCost = []			
		for i in range (1, len(outData["allYearGenerationMWh"])+1):		
			revLevelizedCost.append(Rate_Levelized_TaxEquity*outData["allYearGenerationMWh"][i])
			NPVRevTaxEquity = NPVRevTaxEquity + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
		nValue = NPVRevTaxEquity					
		x = x + 100.0		
		Rate_Levelized_TaxEquity = x/100.0							
	#Second Loop
	while ((x > 2500) and (nValue > nGoal)):
		NPVRevTaxEquity = 0
		revLevelizedCost = []			
		for i in range (1, len(outData["allYearGenerationMWh"])+1):		
			revLevelizedCost.append(Rate_Levelized_TaxEquity*outData["allYearGenerationMWh"][i])
			NPVRevTaxEquity = NPVRevTaxEquity + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
		nValue = NPVRevTaxEquity				
		x = x - 10.0		
		Rate_Levelized_TaxEquity = x/100.0							
	#Third Loop		
	while ((x < 20000) and (nValue < nGoal)):
		NPVRevTaxEquity = 0
		revLevelizedCost = []			
		for i in range (1, len(outData["allYearGenerationMWh"])+1):		
			revLevelizedCost.append(Rate_Levelized_TaxEquity*outData["allYearGenerationMWh"][i])
			NPVRevTaxEquity = NPVRevTaxEquity + revLevelizedCost[i-1]/(math.pow(1+0.0232,i))
		nValue = NPVRevTaxEquity				
		x = x + 1.0		
		Rate_Levelized_TaxEquity = x/100.0					

	#PPA
	#TEI Calcs - Achieved Return [AW 21]
	   	#[AK]  		
	MACRDepreciation = []
	MACRDepreciation.append(-0.99*0.2*(outData["totalCost"]-outData["totalCost"]*0.5*0.9822*0.3))
	MACRDepreciation.append(-0.99*0.32*(outData["totalCost"]-outData["totalCost"]*0.5*0.9822*0.3))
	MACRDepreciation.append(-0.99*0.192*(outData["totalCost"]-outData["totalCost"]*0.5*0.9822*0.3))	
	MACRDepreciation.append(-0.99*0.1152*(outData["totalCost"]-outData["totalCost"]*0.5*0.9822*0.3))
	MACRDepreciation.append(-0.99*0.1152*(outData["totalCost"]-outData["totalCost"]*0.5*0.9822*0.3))		
	MACRDepreciation.append(-0.99*0.0576*(outData["totalCost"]-outData["totalCost"]*0.5*0.9822*0.3))	
	#[AI] [AL]	[AN]
	cashRevenueTEI = [] 	                          	#[AI]
	slDepreciation = []		                            #[AL]
	totalDistributions = []                         	#[AN]	
	cashRevenueTEI.append(-outData["totalCost"]*0.53)				
	for i in range (1,7):
		cashRevenueTEI.append(EBITDATE[i-1]*0.99)
		slDepreciation.append(outData["totalCost"]/25)	
		totalDistributions.append(-cashRevenueTEI[i])	
    #[AJ]						
	ITC = outData["totalCost"]*0.9822*0.3*0.99 		    
    #[AM]						
	taxableIncLoss = [0]  	     
	taxableIncLoss.append(cashRevenueTEI[1]+MACRDepreciation[0])	
    #[AO]		
	capitalAcct = []	                            	
	capitalAcct.append(outData["totalCost"]*0.53)
	condition = capitalAcct[0] - 0.5*ITC + taxableIncLoss[1] + totalDistributions[0]
	if condition > 0:
		capitalAcct.append(condition)
	else:
		capitalAcct.append(0)
	#[AQ]	
	ratioTE = [0]  								
    #[AP]		     
	reallocatedIncLoss = []		            
	#AO-1 + AN + AI + AK + AJ  
	for i in range (0, 5):     
		reallocatedIncLoss.append(capitalAcct[i+1] + totalDistributions[i+1] + MACRDepreciation[i+1] + cashRevenueTEI[i+2])
		ratioTE.append(reallocatedIncLoss[i]/(cashRevenueTEI[i+2] + MACRDepreciation[i+1]))
		taxableIncLoss.append(cashRevenueTEI[i+2]+MACRDepreciation[i+1]-ratioTE[i+1]*(MACRDepreciation[i+1]-totalDistributions[i+1]))			
		condition = capitalAcct[i+1] + taxableIncLoss[i+2] + totalDistributions[i+1]
		if condition > 0:
			capitalAcct.append(condition)
		else:
			capitalAcct.append(0)

	#[AR]
	taxesBenefitLiab = [0]
	for i in range (1, 7):
		taxesBenefitLiab.append(-taxableIncLoss[i]*0.35)
    #[AS] [AT}]
	buyoutAmount = 0	
	taxFromBuyout = 0		
	for i in range (0, len(EBITDATEREDUCED)):
		buyoutAmount = buyoutAmount + .05*EBITDATEREDUCED[i]/(math.pow(1.12,(i+1)))
	taxFromBuyout = -buyoutAmount*0.35
	#[AU] [AV]	
	totalCashTax = []
	cumulativeCashTax = [0]			
	for i in range (0, 7):
		if i == 1:
			totalCashTax.append(cashRevenueTEI[i] + ITC + taxesBenefitLiab[i] + 0 + 0)	
			cumulativeCashTax.append(cumulativeCashTax[i] + totalCashTax[i])				
		elif i == 6:
			totalCashTax.append(cashRevenueTEI[i] + 0 + taxesBenefitLiab[i] + buyoutAmount + taxFromBuyout)		
			cumulativeCashTax.append(cumulativeCashTax[i] + totalCashTax[i] + buyoutAmount + taxFromBuyout)					
		else:
			totalCashTax.append(cashRevenueTEI[i] + 0 + taxesBenefitLiab[i] + 0 + 0)
			cumulativeCashTax.append(cumulativeCashTax[i] + totalCashTax[i])						
	#[AW21]
	if (cumulativeCashTax[7] > 0):
		cumulativeIRR = round(irr(totalCashTax), 4)		
	else:
		cumulativeIRR = 0

	#Master Output [Tax Equity]		
	outData["levelCostTaxEquity"] = Rate_Levelized_TaxEquity
	outData["costPanelTaxEquity"] = abs(NPVLoanTaxEquity/numberPanels)
	outData["cost10WPanelTaxEquity"] = (float(outData["costPanelTaxEquity"])/inputDict["panelSize"])*10

	return cumulativeIRR

#Maps zipcode from excel data to city, state, lat/lon 
#From excel file at: https://www.gaslampmedia.com/download-zip-code-latitude-longitude-city-state-county-csv/
def zipCodeToclimateName(zipCode, test):
	def compareLatLon(LatLon, LatLon2):
		differenceLat = float(LatLon[0]) - float(LatLon2[0]) 
		differenceLon = float(LatLon[1]) - float(LatLon2[1])
		distance = math.sqrt(math.pow(differenceLat, 2) + math.pow(differenceLon,2))
		return distance

	#only has A,  and V
	def safeListdir(path):
		try: return os.listdir(path)
		except:	return []

	if (test == "True"):
		path = "../data/Climate/"
		climateNames = [x[:-5] for x in safeListdir(path)]    	
	else:
		path = "./data/Climate/"
		climateNames = [x[:-5] for x in safeListdir(path)]
	climateCity = []
	lowestDistance = 1000


	try:
		#Parse .csv file with city/state zip codes and lat/lon
		
		if (test == "True"):
			zipCodeCSVDirectory = os.path.abspath("../static/") + "\zip_codes_states.csv"
		else:
			zipCodeCSVDirectory = os.path.abspath("./static/") + "\zip_codes_states.csv"				
		with open(zipCodeCSVDirectory, 'rt') as f:
		     reader = csv.reader(f, delimiter=',') 
		     for row in reader:
		          for field in row:
		              if field == zipCode:
		                  zipState = row[4] 
		                  zipCity = row[3]
		                  ziplatlon  = row[1], row[2]

		#Looks for climate data by looking at all cities in that state
		#Should be change to check other states too 
		#Filter only the cities in that state
		for x in range(0, len(climateNames)):	
			if (zipState+"-" in climateNames[x]):
				climateCity.append(climateNames[x])	
		climateCity = [w.replace(zipState+"-", '') for w in climateCity]	
	    #Parse the cities distances to zipcode city to determine closest climate
		for x in range (0,len(climateCity)):				
			with open(zipCodeCSVDirectory, 'rt') as f:
				reader = csv.reader(f, delimiter=',') 
				for row in reader:
					if ((row[4].lower() == zipState.lower()) and (row[3].lower() == str(climateCity[x]).lower())):
						climatelatlon  = row[1], row[2]   
	                	distance = compareLatLon(ziplatlon, climatelatlon)                	
	                	if (distance < lowestDistance):
	                		lowestDistance = distance
	                		found = x	
		climateName = zipState + "-" + climateCity[found]
		return climateName
	except:
		return "NULL"

def _runningSum(inList):
	''' Give a list of running sums of inList. '''
	return [sum(inList[:i+1]) for (i,val) in enumerate(inList)]

def cancel(modelDir):
	''' solarSunda runs so fast it's pointless to cancel a run. '''
	pass

def _tests():	
	# Variables
	workDir = pJoin(__metaModel__._omfDir,"data","Model")
	# TODO: Fix inData because it's out of date.
	inData = {"simStartDate": "2013-01-01",
		"simLengthUnits": "hours",
		"modelType": "solarSunda",
		"zipCode": "90210",
		"landOwnership": "Purchased", #Leased, Purchased, or Owned
		"costAcre": "10000",
		"systemSize":"1000",
		"moduleCost": "0.70",
		"rackCost": "0.137",
		"inverterCost": "61963",		
		"mechLabor": "35",
		"elecLabor": "50",
		"pmCost": "15000",
		"interCost": "25000",
		"devCost": "2",
		"EPCRate": "3",
		"distAdder": "0",
		"discRate": "2.32",
		"loanRate": "2.00",
		"NCREBRate": "4.06",
		"taxLeaseRate": "7.20",
		"taxEquityReturn": "8.50",	
		"firstYearEnergyCostPPA": "55",
		"annualEscRatePPA": "2",		
		"lifeSpan": "25",
		"degradation": "0.5",
		"derate": "87",
		"inverterEfficiency": "96",
		"tilt": "True",
		"manualTilt":"34.65",	
		"trackingMode":"0",
		"azimuth":"180",
		"runTime": "",
		"rotlim":"45.0",
		"gamma":"-0.45",
		"test": "True"}
	modelLoc = pJoin(workDir,"admin","Automated solarSunda Testing")	
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# No-input template.
	#renderAndShow(template)
	# Run the model.
	run(modelLoc, inData)
	# Show the output.
	#renderAndShow(template, modelDir = modelLoc)
	# # Delete the model.
	# time.sleep(2)
	# shutil.rmtree(modelLoc)

if __name__ == '__main__':
	_tests()

	'''		'''