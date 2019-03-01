''' Calculate solar photovoltaic system output using our special financial model. '''

import json, os, sys, tempfile, webbrowser, time, shutil, subprocess, math, datetime as dt
from numpy import npv, pmt, ppmt, ipmt, irr
from os.path import join as pJoin
from os import walk
from jinja2 import Template
from random import random
import traceback, csv
from omf.models import __neoMetaModel__
from __neoMetaModel__ import *

# OMF imports
import omf.feeder as feeder
from omf.solvers import nrelsam2013
from omf.weather import zipCodeToClimateName

# Model metadata:
modelName, template = metadata(__file__)
tooltip = "The solarSunda model allows you to run multiple instances of the SUNDA Solar Costing Financing Screening Tool and compare their output visually."
hidden = False

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	#Set static input data
	simLength = 8760
	simStartDate = "2013-01-01"
	# Set the timezone to be UTC, it won't affect calculation and display, relative offset handled in pvWatts.html
	startDateTime = simStartDate + " 00:00:00 UTC"		
	simLengthUnits = "hours"
	# Associate zipcode to climate data
	inputDict["climateName"] = zipCodeToClimateName(inputDict["zipCode"])
	inverterSizeAC = float(inputDict.get("inverterSize",0))
	if (inputDict.get("systemSize",0) == "-"):
		arraySizeDC = 1.3908 * inverterSizeAC
	else:
		arraySizeDC = float(inputDict.get("systemSize",0))
	numberPanels = (arraySizeDC * 1000/305)
	# Set constants
	panelSize = 305		
	trackingMode = 0
	rotlim = 45.0
	gamma = 0.45
	if (inputDict.get("tilt",0) == "-"):
		tilt_eq_lat = 1.0
		manualTilt = 0.0
	else:
		tilt_eq_lat = 0.0
		manualTilt = float(inputDict.get("tilt",0))
	numberInverters = math.ceil(inverterSizeAC/1000/0.5)			
	# Copy specific climate data into model directory
	shutil.copy(pJoin(__neoMetaModel__._omfDir, "data", "Climate", inputDict["climateName"] + ".tmy2"),
		pJoin(modelDir, "climate.tmy2"))
	# Set up SAM data structures.
	ssc = nrelsam2013.SSCAPI()
	dat = ssc.ssc_data_create()
	# Required user inputs.
	ssc.ssc_data_set_string(dat, "file_name", modelDir + "/climate.tmy2")
	ssc.ssc_data_set_number(dat, "system_size", arraySizeDC)
	ssc.ssc_data_set_number(dat, "derate", float(inputDict.get("inverterEfficiency", 96))/100 * float(inputDict.get("nonInverterEfficiency", 87))/100)
	ssc.ssc_data_set_number(dat, "track_mode", float(trackingMode))
	ssc.ssc_data_set_number(dat, "azimuth", float(inputDict.get("azimuth", 180)))
	# Advanced inputs with defaults.
	ssc.ssc_data_set_number(dat, "rotlim", float(rotlim))
	ssc.ssc_data_set_number(dat, "gamma", float(-gamma/100))
	ssc.ssc_data_set_number(dat, "tilt", manualTilt)
	ssc.ssc_data_set_number(dat, "tilt_eq_lat", 0.0)
	# Run PV system simulation.
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)
	# Timestamp output.
	outData = {}
	outData["timeStamps"] = [dt.datetime.strftime(
		dt.datetime.strptime(startDateTime[0:19],"%Y-%m-%d %H:%M:%S") +
		dt.timedelta(**{simLengthUnits:x}),"%Y-%m-%d %H:%M:%S") + " UTC" for x in range(simLength)]
	# Geodata output.
	outData["minLandSize"] = round((arraySizeDC/1390.8*5 + 1)*math.cos(math.radians(22.5))/math.cos(math.radians(30.0)),0)
	landAmount = float(inputDict.get("landAmount", 6.0))
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
	# Calculate clipping.
	outData["powerOutputAc"] = ssc.ssc_data_get_array(dat, "ac")
	invSizeWatts = inverterSizeAC * 1000
	outData["powerOutputAcInvClipped"] = [x if x < invSizeWatts else invSizeWatts for x in outData["powerOutputAc"]]
	try:
		outData["percentClipped"] = 100 * (1.0 - sum(outData["powerOutputAcInvClipped"]) / sum(outData["powerOutputAc"]))
	except ZeroDivisionError:
		outData["percentClipped"] = 0.0
	#One year generation
	outData["oneYearGenerationWh"] = sum(outData["powerOutputAcInvClipped"])
	#Annual generation for all years
	loanYears = 25
	outData["allYearGenerationMWh"] = {}
	outData["allYearGenerationMWh"][1] = float(outData["oneYearGenerationWh"])/1000000
	# outData["allYearGenerationMWh"][1] = float(2019.576)
	for i in range (2, loanYears+1):
		outData["allYearGenerationMWh"][i] = float(outData["allYearGenerationMWh"][i-1]) * (1 - float(inputDict.get("degradation", 0.8))/100)
	# Summary of Results.
	######
	### Total Costs (sum of): Hardware Costs, Design/Engineering/PM/EPC/Labor Costs, Siteprep Costs, Construction Costs, Installation Costs, Land Costs
	######
	### Hardware Costs 
	pvModules = arraySizeDC * float(inputDict.get("moduleCost",0))*1000 #off by 4000
	racking = arraySizeDC * float(inputDict.get("rackCost",0))*1000
	inverters = numberInverters * float(inputDict.get("inverterCost",0))
	inverterSize = inverterSizeAC
	if (inverterSize <= 250):
		gear = 15000
	elif (inverterSize <= 600):
		gear = 18000
	else:
		gear = inverterSize/1000 * 22000
	balance = inverterSizeAC * 1.3908 * 134
	combiners = math.ceil(numberPanels/19/24) * float(1800)  #*
	wireManagement = arraySizeDC * 1.5
	transformer = 1 * 28000
	weatherStation = 1 * 12500
	shipping = 1.02
	hardwareCosts = (pvModules + racking + inverters + gear + balance + combiners + wireManagement  + transformer + weatherStation) * shipping
	### Design/Engineering/PM/EPC/Labor Costs 
	EPCmarkup = float(inputDict.get("EPCRate",0))/100 * hardwareCosts
	#designCosts = float(inputDict.get("mechLabor",0))*160 + float(inputDict.get("elecLabor",0))*75 + float(inputDict.get("pmCost",0)) + EPCmarkup
	hoursDesign = 160*math.sqrt(arraySizeDC/1390)
	hoursElectrical = 80*math.sqrt(arraySizeDC/1391)
	designLabor = 65*hoursDesign
	electricalLabor = 75*hoursElectrical
	laborDesign = designLabor + electricalLabor + float(inputDict.get("pmCost",0)) + EPCmarkup
	materialDesign = 0
	designCosts = materialDesign + laborDesign
	### Siteprep Costs 
	surveying = 2.25 * 4 * math.sqrt(landAmount*43560)
	concrete = 8000 * math.ceil(numberInverters/2)
	fencing = 6.75 * 4 * math.sqrt(landAmount*43560)
	grading = 2.5 * 4 * math.sqrt(landAmount*43560)
	landscaping = 750 * landAmount
	siteMaterial = 8000 + 600 + 5500 + 5000 + surveying + concrete + fencing + grading + landscaping + 5600
	blueprints = float(inputDict.get("mechLabor",0))*12
	mobilization = float(inputDict.get("mechLabor",0))*208
	mobilizationMaterial = float(inputDict.get("mechLabor",0))*19.98
	siteLabor = blueprints + mobilization + mobilizationMaterial
	sitePrep = siteMaterial + siteLabor
	### Construction Costs (Office Trailer, Skid Steer, Storage Containers, etc) 
	constrEquip = 6000 + math.sqrt(landAmount)*16200
	### Installation Costs 
	moduleAndRackingInstall = numberPanels * (15.00 + 12.50 + 1.50)
	pierDriving = 1 * arraySizeDC*20
	balanceInstall = 1 * arraySizeDC*100
	installCosts = moduleAndRackingInstall + pierDriving + balanceInstall + float(inputDict.get("elecLabor",0)) * (72 + 60 + 70 + 10 + 5 + 30 + 70)
	### Land Costs 
	if (str(inputDict.get("landOwnership",0)) == "Owned" or (str(inputDict.get("landOwnership",0)) == "Leased")):
		landCosts = 0
	else:
		landCosts = float(inputDict.get("costAcre",0))*landAmount
	######
	### Total Costs 
	######
	totalCosts = hardwareCosts + designCosts + sitePrep + constrEquip + installCosts + landCosts
	totalFees= float(inputDict.get("devCost",0))/100 * totalCosts
	outData["totalCost"] = totalCosts + totalFees + float(inputDict.get("interCost",0))
	# Add to Pie Chart
	outData["costsPieChart"] = [["Land", landCosts],
		["Design/Engineering/PM/EPC", designCosts],
		["PV Modules", pvModules*shipping],
		["Racking", racking*shipping],
		["Inverters & Switchgear", (inverters+gear)*shipping],
		["BOS", hardwareCosts - pvModules*shipping - racking*shipping - (inverters+gear)*shipping],
		["Site Prep, Constr. Eq. and Installation", (siteMaterial + constrEquip) + (siteLabor + installCosts)]]
	# Cost per Wdc
	outData["costWdc"] = (totalCosts + totalFees + float(inputDict.get("interCost",0))) / (arraySizeDC * 1000)
	outData["capFactor"] = float(outData["oneYearGenerationWh"])/(inverterSizeAC*1000*365.25*24) * 100
	######
	### Loans calculations for Direct, NCREB, Lease, Tax-equity, and PPA
	######
	### Full Ownership, Direct Loan
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
	## Output - Direct Loan Formulas
	projectCostsDirect = 0
	#Output - Direct Loan [D]
	payment = pmt(float(inputDict.get("loanRate",0))/100, loanYears, outData["totalCost"])
	interestDirectPI = outData["totalCost"] * float(inputDict.get("loanRate",0))/100
	principleDirectPI = (-payment - interestDirectPI)
	patronageCapitalRetiredDPI = 0
	netFinancingCostsDirect = -(principleDirectPI + interestDirectPI - patronageCapitalRetiredDPI)
	#Output - Direct Loan [E] [F] [G] [H]
	firstYearOPMainCosts = (1.25 * arraySizeDC * 12)
	firstYearInsuranceCosts = (0.37 * outData["totalCost"]/100)
	if (inputDict.get("landOwnership",0) == "Leased"):
		firstYearLandLeaseCosts = float(inputDict.get("costAcre",0))*landAmount
	else:
		firstYearLandLeaseCosts = 0
	for i in range (1, len(outData["allYearGenerationMWh"])+1):
		OMInsuranceETCDirect.append(-firstYearOPMainCosts*math.pow((1 + .01),(i-1)) - firstYearInsuranceCosts*math.pow((1 + .025),(i-1)) - firstYearLandLeaseCosts*math.pow((1 + .01),(i-1)))
		distAdderDirect.append(float(inputDict.get("distAdder",0))*outData["allYearGenerationMWh"][i])
		netCoopPaymentsDirect.append(OMInsuranceETCDirect[i-1] + netFinancingCostsDirect)
		costToCustomerDirect.append((netCoopPaymentsDirect[i-1] - distAdderDirect[i-1]))
	#Output - Direct Loan [F53] 
	NPVLoanDirect = npv(float(inputDict.get("discRate",0))/100, [0,0] + costToCustomerDirect)
	NPVallYearGenerationMWh = npv(float(inputDict.get("discRate",0))/100, [0,0] + outData["allYearGenerationMWh"].values())
	Rate_Levelized_Direct = -NPVLoanDirect/NPVallYearGenerationMWh	
	#Master Output [Direct Loan]
	outData["levelCostDirect"] = Rate_Levelized_Direct
	outData["costPanelDirect"] = abs(NPVLoanDirect/numberPanels)
	outData["cost10WPanelDirect"] = (float(outData["costPanelDirect"])/panelSize)*10
	### NCREBs Financing
	ncrebsRate = float(inputDict.get("NCREBRate",4.060))/100
	ncrebBorrowingRate = 1.1 * ncrebsRate
	ncrebPaymentPeriods = 44
	ncrebCostToCustomer = []
	# TODO ASAP: FIX ARRAY OFFSETS START 0
	for i in range (1, len(outData["allYearGenerationMWh"])+1):
		coopLoanPayment = 2 * pmt(ncrebBorrowingRate/2.0, ncrebPaymentPeriods, outData["totalCost"]) if i <= ncrebPaymentPeriods / 2 else 0
		ncrebsCredit = -0.7 * (ipmt(ncrebsRate / 2, 2 * i - 1, ncrebPaymentPeriods, outData["totalCost"])
			+ ipmt(ncrebsRate / 2, 2 * i, ncrebPaymentPeriods, outData["totalCost"])) if i <= ncrebPaymentPeriods / 2 else 0
		financingCost = ncrebsCredit + coopLoanPayment
		omCost = OMInsuranceETCDirect[i - 1]
		netCoopPayments = financingCost + omCost
		distrAdder = distAdderDirect[i - 1]
		costToCustomer = netCoopPayments + distrAdder
		ncrebCostToCustomer.append(costToCustomer)
	NPVLoanNCREB = npv(float(inputDict.get("discRate", 0))/100, [0,0] + ncrebCostToCustomer)
	Rate_Levelized_NCREB = -NPVLoanNCREB/NPVallYearGenerationMWh	
	outData["levelCostNCREB"] = Rate_Levelized_NCREB
	outData["costPanelNCREB"] = abs(NPVLoanNCREB/numberPanels)
	outData["cost10WPanelNCREB"] = (float(outData["costPanelNCREB"])/panelSize)*10
	### Lease Buyback Structure
	#Output - Lease [C]
	projectCostsLease = outData["totalCost"]
	#Output - Lease [D]
	leasePaymentsLease = []
	#Output - Lease [E]
	OMInsuranceETCLease = OMInsuranceETCDirect
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
	## Tax Lease Formulas
	#Output - Lease [D]
	for i in range (0, 12):
		leaseRate = float(inputDict.get("taxLeaseRate",0))/100.0
		if i>8: # Special behavior in later years:
			leaseRate = leaseRate - 0.0261
		leasePaymentsLease.append(-1*projectCostsLease/((1.0-(1.0/(1.0+leaseRate)**12))/(leaseRate)))
	# Last year is different.
	leasePaymentsLease[11] += -0.2*projectCostsLease
	for i in range (12, 25):
		leasePaymentsLease.append(0)
	#Output - Lease [G]	[H]
	for i in range (1, len(outData["allYearGenerationMWh"])+1):
		netCoopPaymentsLease.append(OMInsuranceETCLease[i-1]+leasePaymentsLease[i-1])
		costToCustomerLease.append(netCoopPaymentsLease[i-1]-distAdderLease[i-1])
	#Output - Lease [H44]. Note the extra year at the zero point to get the discounting right.
	NPVLease = npv(float(inputDict.get("discRate", 0))/100, [0,0]+costToCustomerLease)
	#Output - Lease [H49] (Levelized Cost Three Loops)
	Rate_Levelized_Lease = -NPVLease/NPVallYearGenerationMWh
	#Master Output [Lease]
	outData["levelCostTaxLease"] = Rate_Levelized_Lease
	outData["costPanelTaxLease"] = abs(NPVLease/numberPanels)
	outData["cost10WPanelTaxLease"] = (float(outData["costPanelTaxLease"])/float(panelSize))*10
	### Tax Equity Flip Structure
	# Tax Equity Flip Function
	def taxEquityFlip(PPARateSixYearsTE, discRate, totalCost, allYearGenerationMWh, distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels):
		#Output Tax Equity Flip [C]
		coopInvestmentTaxEquity = -totalCost*(1-0.53)
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
		#Output Tax Equity Flip [L64]
		NPVLoanTaxEquity = 0
		#Output Tax Equity Flip [F72]
		Rate_Levelized_Equity = 0
		## Tax Equity Flip Formulas
		#Output Tax Equity Flip [D]
		#TEI Calcs [E]
		financeCostOfCashTE = 0
		coopFinanceRateTE = 2.7/100
		if (coopFinanceRateTE == 0):
			financeCostOfCashTE = 0
		else:
			payment = pmt(coopFinanceRateTE, loanYears, -coopInvestmentTaxEquity)
		financeCostCashTaxEquity = payment
		#Output Tax Equity Flip [E]
		SPERevenueTE = []
		for i in range (1, len(allYearGenerationMWh)+1):
			SPERevenueTE.append(PPARateSixYearsTE * allYearGenerationMWh[i])
			if ((i>=1) and (i<=6)):
				cashToSPEOForPPATE.append(-SPERevenueTE[i-1])
			else:
				cashToSPEOForPPATE.append(0)
		#Output Tax Equity Flip [F]
		derivedCostEnergyTE = cashToSPEOForPPATE[0]/allYearGenerationMWh[1]
		#Output Tax Equity Flip [G]
		#TEI Calcs [F]	[U] [V]
		landLeaseTE = []
		OMTE = []
		insuranceTE = []
		for i in range (1, len(allYearGenerationMWh)+1):
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
		cashRevenueTE = -totalCost * (1 - 0.53)
		buyoutAmountTE = 0
		for i in range (1, len(EBITDATEREDUCED) + 1):
			buyoutAmountTE = buyoutAmountTE + EBITDATEREDUCED[i-1]/(math.pow(1+0.12,i))
		buyoutAmountTE = buyoutAmountTE * 0.05
		cashFromBlockerTE = - (buyoutAmountTE) + 0.0725 * cashRevenueTE
		#Output Tax Equity Flip [K] [L]
		for i in range (1, len(allYearGenerationMWh)+1):
			if (i==6):
				netCoopPaymentsTaxEquity.append(financeCostCashTaxEquity + cashToSPEOForPPATE[i-1] + cashFromSPEToBlockerTE[i-1] + OMInsuranceETCTE[i-1] + cashFromBlockerTE)
			else:
				netCoopPaymentsTaxEquity.append(financeCostCashTaxEquity + cashFromSPEToBlockerTE[i-1] + cashToSPEOForPPATE[i-1] + OMInsuranceETCTE[i-1])
			costToCustomerTaxEquity.append(netCoopPaymentsTaxEquity[i-1] - distAdderTaxEquity[i-1])
		#Output Tax Equity Flip [L37]
		NPVLoanTaxEquity = npv(float(inputDict.get("discRate",0))/100, [0, 0] + costToCustomerTaxEquity)
		#Output - Tax Equity [F42] 
		Rate_Levelized_TaxEquity = -NPVLoanTaxEquity/NPVallYearGenerationMWh
		#TEI Calcs - Achieved Return [AW 21]
			#[AK]
		MACRDepreciation = []
		MACRDepreciation.append(-0.99*0.2*(totalCost-totalCost*0.5*0.9822*0.3))
		MACRDepreciation.append(-0.99*0.32*(totalCost-totalCost*0.5*0.9822*0.3))
		MACRDepreciation.append(-0.99*0.192*(totalCost-totalCost*0.5*0.9822*0.3))
		MACRDepreciation.append(-0.99*0.1152*(totalCost-totalCost*0.5*0.9822*0.3))
		MACRDepreciation.append(-0.99*0.1152*(totalCost-totalCost*0.5*0.9822*0.3))
		MACRDepreciation.append(-0.99*0.0576*(totalCost-totalCost*0.5*0.9822*0.3))
		#[AI] [AL]	[AN]
		cashRevenueTEI = [] 	                          	#[AI]
		slDepreciation = []		                            #[AL]
		totalDistributions = []                         	#[AN]
		cashRevenueTEI.append(-totalCost*0.53)
		for i in range (1,7):
			cashRevenueTEI.append(EBITDATE[i-1]*0.99)
			slDepreciation.append(totalCost/25)
			totalDistributions.append(-cashRevenueTEI[i])
		#[AJ]						
		ITC = totalCost*0.9822*0.3*0.99
		#[AM]						
		taxableIncLoss = [0]
		taxableIncLoss.append(cashRevenueTEI[1]+MACRDepreciation[0])
		#[AO]		
		capitalAcct = []
		capitalAcct.append(totalCost*0.53)
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
		#[AS] [AT]
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
		# Deleteme: Variable Dump for debugging
		# variableDump = {}
		# variableDump["TaxEquity"] = {}
		# variableDump["TaxEquity"]["coopInvestmentTaxEquity"] = coopInvestmentTaxEquity
		# variableDump["TaxEquity"]["financeCostCashTaxEquity"] = financeCostCashTaxEquity
		# variableDump["TaxEquity"]["cashToSPEOForPPATE"] = cashToSPEOForPPATE
		# variableDump["TaxEquity"]["derivedCostEnergyTE"] = derivedCostEnergyTE
		# variableDump["TaxEquity"]["OMInsuranceETCTE"] = OMInsuranceETCTE
		# variableDump["TaxEquity"]["cashFromSPEToBlockerTE"] = cashFromSPEToBlockerTE
		# variableDump["TaxEquity"]["cashFromBlockerTE"] = cashFromBlockerTE
		# variableDump["TaxEquity"]["distAdderTaxEquity"] = distAdderTaxEquity
		# variableDump["TaxEquity"]["netCoopPaymentsTaxEquity"] = netCoopPaymentsTaxEquity
		# variableDump["TaxEquity"]["NPVLoanTaxEquity"] = NPVLoanTaxEquity
		return cumulativeIRR, Rate_Levelized_TaxEquity, NPVLoanTaxEquity
	# Function Calls Mega Sized Tax Equity Function Above
	z = 0
	PPARateSixYearsTE = z / 100
	nGoal = float(inputDict.get("taxEquityReturn",0))/100
	nValue = 0
	for p in range (0, 3):
		while ((z < 50000) and (nValue < nGoal)):
			achievedReturnTE, Rate_Levelized_TaxEquity, NPVLoanTaxEquity = taxEquityFlip(PPARateSixYearsTE, inputDict.get("discRate", 0), outData["totalCost"], outData["allYearGenerationMWh"], distAdderDirect, loanYears, firstYearLandLeaseCosts, firstYearOPMainCosts, firstYearInsuranceCosts, numberPanels)
			nValue = achievedReturnTE
			z = z + math.pow(10,p)
			PPARateSixYearsTE = z/100.0
	z = z - math.pow(10,p)	
	PPARateSixYearsTE = z/100
	#Master Output [Tax Equity]
	outData["levelCostTaxEquity"] = Rate_Levelized_TaxEquity
	outData["costPanelTaxEquity"] = abs(NPVLoanTaxEquity/numberPanels)
	outData["cost10WPanelTaxEquity"] = (float(outData["costPanelTaxEquity"])/panelSize)*10
	### PPA Comparison
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
	## PPA Formulas
	#Output - PPA [G] [H]
	for i in range (1, len(outData["allYearGenerationMWh"])+1):
		netCoopPaymentsPPA.append(-outData["allYearGenerationMWh"][i]*float(inputDict.get("firstYearEnergyCostPPA",0))*math.pow((1 + float(inputDict.get("annualEscRatePPA", 0))/100),(i-1)))
		costToCustomerPPA.append(netCoopPaymentsPPA[i-1]-distAdderPPA[i-1])
	#Output - PPA [H58] 
	NPVLoanPPA = npv(float(inputDict.get("discRate", 0))/100, [0,0]+costToCustomerPPA)
	#Output - PPA [F65] 
	Rate_Levelized_PPA = -NPVLoanPPA/NPVallYearGenerationMWh
	#Master Output [PPA]
	outData["levelCostPPA"] = Rate_Levelized_PPA
	outData["firstYearCostKWhPPA"] = float(inputDict.get("firstYearEnergyCostPPA",0))
	outData["yearlyEscalationPPA"] = float(inputDict.get("annualEscRatePPA", 0))
	# Add all Levelized Costs to Output
	outData["LevelizedCosts"] = [["Direct Loan", Rate_Levelized_Direct],
		["NCREBs Financing", Rate_Levelized_NCREB],
		["Lease Buyback", Rate_Levelized_Lease],
		["Tax Equity Flip", Rate_Levelized_TaxEquity]]
	outData["LevelizedCosts"].append({"name":"PPA Comparison", "y":Rate_Levelized_PPA, "color":"gold"})
	# Stdout/stderr.
	outData["stdout"] = "Success"
	outData["stderr"] = ""
	return outData

def _runningSum(inList):
	''' Give a list of running sums of inList. '''
	return [sum(inList[:i+1]) for (i,val) in enumerate(inList)]

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {"modelType": modelName,
		#Cooperative
		"zipCode": "64735",
		"inverterSize":"1000",
		"systemSize":"1390.8",
		"landOwnership": "Owned", #Leased, Purchased, or Owned
		"landAmount": "6",
		"costAcre": "10000",
		"moduleCost": "0.70",
		"rackCost": "0.137",
		"inverterCost": "107000",
		"pmCost": "15000",
		"EPCRate": "3",
		"mechLabor": "35",
		"elecLabor": "50",
		"devCost": "2",
		"interCost": "25000",
		"distAdder": "0",
		#Financing Information
		"discRate": "2.32",
		"loanRate": "2.00",
		"NCREBRate": "4.06",
		"taxLeaseRate": "-4.63",
		"taxEquityReturn": "8.50",
		#PPA Information
		"firstYearEnergyCostPPA": "57.5",
		"annualEscRatePPA": "3",
		#Misc
		"lifeSpan": "25",
		"degradation": "0.8",
		"inverterEfficiency": "96",
		"nonInverterEfficiency": "87",
		"tilt": "-",
		"trackingMode":"0",
		"module_type":"1", #PVWatts v5 feature: 1 = premium
		"azimuth":"180"
	}
	return __neoMetaModel__.new(modelDir, defaultInputs)

def _tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass
	# Create New.
	new(modelLoc)
	# Pre-run.
	renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()