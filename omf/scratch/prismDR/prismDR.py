'''
    Created on July 15, 2015
    prismDR(xxxxxxx)
    
    Implements the PRISM DR model based on xxxxxxx
    
    Input:xxxxxxx
    Output:
    Example:

    
    @author: trevorhardy
    '''

import sys
import warnings
import csv
import datetime
import calendar
import math
import operator
import copy

#def findOffPeakRate():

#def calcLoadImpacts():

def importLoad(file_path):
	load_file = open(file_path, 'r')
	reader = csv.reader(load_file)
	load = list(float(row[0]) for row in reader)
	load_file.close
	return load

def importElast(file_path):
	#DEPRICATED: No longer used as funcationalization passes these values in as part of the input dictionary.
	elast = dict()
	elast_file = open(file_path, 'rU')
	reader = csv.reader(elast_file)
	temp = list(float(row[0]) for row in reader)
	elast['sub'] = temp[0]
	elast['daily'] = temp[1]
	elast_file.close
	return elast

def importRates(file_path):
	#DEPRICATED: No longer used as funcationalization passes these values in as part of the input dictionary.
	rates = dict()
	rate_file = open(file_path, 'rU')
	reader = csv.reader(rate_file)
	temp = list(float(row[0]) for row in reader)
	rates['flat'] = temp[0]
	rates['on_peak'] = temp[1]
	rate_file.close
	return rates

def importSchedule(file_path):
	#DEPRICATED: No longer used as funcationalization passes these values in as part of the input dictionary.
	schedule = dict()
	schedule_file = open(file_path, 'rU')
	reader = csv.reader(schedule_file)
	temp = list(int(row[0]) for row in reader)
	schedule['start_month'] = temp[0]
	schedule['stop_month'] = temp[1]
	schedule['start_hour'] = temp[2]
	schedule['stop_hour'] = temp[3]
	schedule_file.close
	return schedule

def calcTimes(prismDRDict):
	start_date = datetime.date(2009,prismDRDict['startMonth'],1)
	last_day =calendar.monthrange(2009, prismDRDict['stopMonth'])
	stop_date = datetime.date(2009,prismDRDict['stopMonth'],last_day[1])
	day_count = stop_date - start_date
	prismDRDict['dayCount']= day_count.days
	start_index = start_date - datetime.date(2009,1,1)
	prismDRDict['startIndex'] = start_index.days * 24
	prismDRDict['stopIndex'] = prismDRDict['startIndex'] + ((prismDRDict['dayCount']+1) * 24) - 1
	prismDRDict['numMonths'] = prismDRDict['stopMonth'] - prismDRDict['startMonth'] + 1
	prismDRDict['numHoursOn'] = prismDRDict['stopHour'] - prismDRDict['startHour'] + 1
	prismDRDict['numHoursOff'] = (24 - prismDRDict['numHoursOn'])
	prismDRDict['hrsOnPeakWCPP'] = prismDRDict['numHoursOn'] * prismDRDict['numCPPDays']
	prismDRDict['hrsOffPeakWCPP'] = prismDRDict['numHoursOff'] * prismDRDict['numCPPDays']
	prismDRDict['hrsOnPeakWOCPP'] = ((prismDRDict['stopHour'] - prismDRDict['startHour']) * prismDRDict['dayCount']) - prismDRDict['hrsOnPeakWCPP']
	prismDRDict['hrsOffPeakWOCPP'] = ((prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeakWOCPP']) - prismDRDict['hrsOffPeakWCPP']
	prismDRDict['hrsOnPeakPerMonthWCPP'] = float(prismDRDict['hrsOnPeakWCPP']) / float(prismDRDict['numMonths'])
	prismDRDict['hrsOffPeakPerMonthWCPP'] = float(prismDRDict['hrsOffPeakWCPP']) / float(prismDRDict['numMonths'])
	prismDRDict['hrsOnPeakPerMonthWOCPP'] = float(prismDRDict['hrsOnPeakWOCPP']) / float(prismDRDict['numMonths'])
	prismDRDict['hrsOffPeakPerMonthWOCPP'] = float(prismDRDict['hrsOffPeakWOCPP']) / float(prismDRDict['numMonths'])

	#PRISM Impacts Inputs
	print 'Start index:', prismDRDict['startIndex']
	print 'Stop index:', prismDRDict['stopIndex']
	print 'On-peak hours per day:', prismDRDict['numHoursOn']
	print 'Off-peak hours per day:', prismDRDict['numHoursOff']
	print 'C49 (enter value): Total CPP hours on-peak:', prismDRDict['hrsOnPeakWCPP']
	print 'C50 (enter value):Total CPP hours off-peak:', prismDRDict['hrsOffPeakWCPP']
	print 'C51 (enter value):Total non-CPP hours on-peak:', prismDRDict['hrsOnPeakWOCPP']
	print 'C52 (enter value): Total non-CPP hours off-peak:', prismDRDict['hrsOffPeakWOCPP']
	print 'Number of months in cooling season:', prismDRDict['numMonths']
	print 'D49: CPP hours on-peak per month:', prismDRDict['hrsOnPeakPerMonthWCPP']
	print 'D50: CPP hours off-peak per month:', prismDRDict['hrsOffPeakPerMonthWCPP']
	print 'D51: Non-CPP hours on-peak per month:', prismDRDict['hrsOnPeakPerMonthWOCPP']
	print 'D52: Non-CPP hours off-peak per month:', prismDRDict['hrsOffPeakPerMonthWOCPP']
	return prismDRDict

def findCPPDays(prismDRDict):
	#Finds largest load days and designates them CPP days.
	maxCount = 0
	tempLoad = copy.copy(prismDRDict['originalLoadProfile'])
	#tempDict = dict(prismDRDict)
	#tempLoad = tempDict['originalLoadProfile']
	prismDRDict['cppDayIdx'] = []
	while maxCount < prismDRDict['numCPPDays']:
		maxIndex, maxLoad = max(enumerate(tempLoad), key=operator.itemgetter(1))
		#print 'Peak load index', maxIndex
		maxIndex = (maxIndex // 24) * 24 #First hour of day.
		#print 'Peak load start of day', maxIndex
#		print 'maxIndex: ', maxIndex
#		print 'PRE tempLoad first hour: ', tempLoad[maxIndex]
#		print 'PRE origLoad first hour: ', prismDRDict['originalLoadProfile'][maxIndex]
#		print 'PRE tempLoad list length: ', len(tempLoad)
#		print 'PRE origLoad list length: ', len(prismDRDict['originalLoadProfile'])
		tempLoad[maxIndex:maxIndex + 24] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] #Zero-ing out so that we don't consider this day again
#		print 'POST tempLoad first hour: ', tempLoad[maxIndex]
#		print 'POST origLoad first hour: ', prismDRDict['originalLoadProfile'][maxIndex]
#		print 'POST tempLoad list length: ', len(tempLoad)
#		print 'POST origLoad list length: ', len(prismDRDict['originalLoadProfile'])
#		print ' '
		if maxIndex > prismDRDict['startIndex'] & maxIndex < prismDRDict['stopIndex']: #max day was in DR season
			for idx in range(0,24):
				prismDRDict['cppDayIdx'].append(maxIndex + idx)
				#print prismDRDict['cppDayIdx'][-1]
			maxCount+=1
	return prismDRDict



def calcEnergy(prismDRDict):
	prismDRDict['onPeakWOCPPEnergy'] = 0
	prismDRDict['offPeakWOCPPEnergy'] = 0
	prismDRDict['offPeakWCPPEnergy'] = 0
	prismDRDict['onPeakWCPPEnergy'] = 0
	print 'Start Hour:', prismDRDict['startHour']
	print 'Stop Hour:', prismDRDict['stopHour']
	for idx, load in enumerate(prismDRDict['originalLoadProfile']):
		if idx > prismDRDict['startIndex'] & idx < prismDRDict['stopIndex']: #is hour of year in the cooling season?
			hourOfDay  = idx % 24
			#print 'Current hour of day:', hourOfDay
			if idx in prismDRDict['cppDayIdx']:
				if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
					prismDRDict['offPeakWCPPEnergy'] += load
					#print 'CPP off-peak'
				else:
					prismDRDict['onPeakWCPPEnergy'] += load
					#print 'CPP on-peak'
			else:
				if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
					prismDRDict['offPeakWOCPPEnergy'] += load
					#print 'Non-CPP off-peak'
				else:
					prismDRDict['onPeakWOCPPEnergy'] += load
					#print 'Non-CPP on-peak'
	prismDRDict['totalEnergy'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy'] + prismDRDict['offPeakWCPPEnergy']  + prismDRDict['onPeakWCPPEnergy']
	prismDRDict['onPeakWOCPPMonAvgkWh'] = prismDRDict['onPeakWOCPPEnergy']/prismDRDict['numMonths']
	prismDRDict['offPeakWOCPPMonAvgkWh'] = prismDRDict['offPeakWOCPPEnergy']/prismDRDict['numMonths']
	prismDRDict['onPeakWCPPMonAvgkWh'] = prismDRDict['onPeakWCPPEnergy']/prismDRDict['numMonths']
	prismDRDict['offPeakWCPPMonAvgkWh'] = prismDRDict['offPeakWCPPEnergy']/prismDRDict['numMonths']
	prismDRDict['totalMonAvgkWh'] = prismDRDict['totalEnergy']/prismDRDict['numMonths']

	#PRISM Impacts Inputs
	print 'B11 (enter value): CPP On-peak Monthly Average kWh:', prismDRDict['onPeakWCPPMonAvgkWh']
	print 'B12 (enter value): CPP Off-peak Monthly Average kWh:', prismDRDict['offPeakWCPPMonAvgkWh']
	print 'B13 (enter value): Non-CPP On-peak Monthly Average kWh:', prismDRDict['onPeakWOCPPMonAvgkWh']
	print 'B14 (enter value): Non-CPP Off-peak Monthly Average kWh:', prismDRDict['offPeakWOCPPMonAvgkWh']
	print 'B15: Total Monthly Average kWh:', prismDRDict['totalMonAvgkWh']
	return prismDRDict

def calcOffPeak(prismDRDict):
	original_bill = prismDRDict['rateFlat'] * prismDRDict['totalMonAvgkWh']
	prismDRDict['rateOffPeak'] = (original_bill - (prismDRDict['rateCPP']*prismDRDict['onPeakWCPPMonAvgkWh'] + prismDRDict['rateOnPeak']*prismDRDict['onPeakWOCPPMonAvgkWh']))/(prismDRDict['offPeakWCPPMonAvgkWh'] + prismDRDict['offPeakWOCPPMonAvgkWh'])
	#PRISM Impacts Inputs
	print 'E35: Off-peak rate: ', prismDRDict['rateOffPeak']
	return prismDRDict

def calcImpactFactors(prismDRDict):
#	impact_factors = dict()
#	kWh_per_hr_old_on_peak = energyProfile['on_peak']/schedule['hrs_on_peak_per_month']
#	kWh_per_hr_old_off_peak = energyProfile['off_peak']/schedule['hrs_off_peak_per_month']
#	log_factor = math.log(kWh_per_hr_old_on_peak/kWh_per_hr_old_off_peak) + elastcity['sub']*   \
#								(math.log(rates['on_peak']/rates['off_peak']) - math.log(rates['flat']/rates['flat']))
#	kWh_per_hr_old_daily = ((kWh_per_hr_old_on_peak * schedule['num_hours_on']) +
#								(kWh_per_hr_old_off_peak * schedule['num_hours_off']))/24
#	rates['daily_new_peak'] = ((rates['on_peak'] * schedule['num_hours_on'] * kWh_per_hr_old_on_peak) +  \
#								(rates['off_peak'] * schedule['num_hours_off'] * kWh_per_hr_old_off_peak))/  \
#								((schedule['num_hours_on']*kWh_per_hr_old_on_peak)+(schedule['num_hours_off']*kWh_per_hr_old_off_peak))
#	rates['daily_old_peak'] = ((rates['flat'] * schedule['num_hours_on'] * kWh_per_hr_old_on_peak) +  \
#								(rates['flat'] * schedule['num_hours_off'] * kWh_per_hr_old_off_peak))/  \
#								((schedule['num_hours_on']*kWh_per_hr_old_on_peak)+(schedule['num_hours_off']*kWh_per_hr_old_off_peak))
#	kWh_per_hr_new_daily = math.exp(math.log(kWh_per_hr_old_daily) -  \
#								(elastcity['daily'] * (math.log(rates['daily_old_peak']) - math.log(rates['daily_new_peak']))))
#	kWh_per_hr_new_off_peak = ((24/float(schedule['num_hours_off'])) * kWh_per_hr_new_daily)/ \
#								(1+((schedule['num_hours_on']/float(schedule['num_hours_off'])) * math.exp(log_factor)))
#	kWh_per_hr_new_on_peak = kWh_per_hr_new_off_peak  * math.exp(log_factor)
#	kWh_delta_on_peak = kWh_per_hr_new_on_peak - kWh_per_hr_old_on_peak
#	kWh_delta_off_peak = kWh_per_hr_new_off_peak - kWh_per_hr_old_off_peak
#	impact_factors['on_peak'] = kWh_delta_on_peak/kWh_per_hr_old_on_peak
#	impact_factors['off_peak'] = kWh_delta_off_peak/kWh_per_hr_old_off_peak

	#Non-CPP days
	kWhPerHrOldOnPeakWOCPP = prismDRDict['onPeakWOCPPMonAvgkWh']/prismDRDict['hrsOnPeakPerMonthWOCPP'] # B30
	kWhPerHrOldOffPeakWOCPP = prismDRDict['offPeakWOCPPMonAvgkWh']/prismDRDict['hrsOffPeakPerMonthWOCPP'] #C30
	logFactorWOCPP = math.log(kWhPerHrOldOnPeakWOCPP/kWhPerHrOldOffPeakWOCPP) + prismDRDict['elasticitySub'] * (math.log(prismDRDict['rateOnPeak']/prismDRDict['rateOffPeak'] - math.log(prismDRDict['rateFlat']/prismDRDict['rateFlat']))) #B28
	kWhPerHrOldDailyWOCPP = ((kWhPerHrOldOnPeakWOCPP * prismDRDict['numHoursOn']) +
							  (kWhPerHrOldOffPeakWOCPP * prismDRDict['numHoursOff']))/24 #D30
	dailyNewPeakWOCPP = ((prismDRDict['rateOnPeak'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP) + (prismDRDict['rateOffPeak'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D24
	dailyOldPeakWOCPP = ((prismDRDict['rateFlat'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP) + (prismDRDict['rateFlat'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D23
	kWhPerHrNewDailyWOCPP = math.exp(math.log(kWhPerHrOldDailyWOCPP) - (prismDRDict['elasticityDaily'] * (math.log(dailyOldPeakWOCPP) - math.log(dailyNewPeakWOCPP)))) #D31
	kWhPerHrNewOffPeakWOCPP =  ((24/float(prismDRDict['numHoursOff'])) * kWhPerHrNewDailyWOCPP) / (1+((prismDRDict['numHoursOn']/float(prismDRDict['numHoursOff'])) * math.exp(logFactorWOCPP))) #C31
	kWhPerHrNewOnPeakWOCPP  = kWhPerHrNewOffPeakWOCPP * math.exp(logFactorWOCPP) #B31
	kWhDeltaOnPeakWOCPP = kWhPerHrNewOnPeakWOCPP - kWhPerHrOldOnPeakWOCPP #B32
	kWhDeltaOffPeakWOCPP = kWhPerHrNewOffPeakWOCPP - kWhPerHrOldOffPeakWOCPP #C32
	prismDRDict['impactFactorOnPeakWOCPP'] = kWhDeltaOnPeakWOCPP/kWhPerHrOldOnPeakWOCPP #B33
	prismDRDict['impactFactorOffPeakWOCPP'] = kWhDeltaOffPeakWOCPP/kWhPerHrOldOffPeakWOCPP #C33

	#PRISM Impacts per Participant
	print 'B30: kWh per hour, old, on-peak, non-CPP:', kWhPerHrOldOnPeakWOCPP
	print 'C30: kWh per hour, old, off-peak, non-CPP:', kWhPerHrOldOffPeakWOCPP
	print 'B28: Log factor, non-CPP:', logFactorWOCPP
	print 'D30: kWh per hour, old, daily, non-CPP:', kWhPerHrOldDailyWOCPP
	print 'D24: New daily on-peak price, non-CPP:', dailyNewPeakWOCPP
	print 'D23: Old daily on-peak price, non-CPP:', dailyOldPeakWOCPP
	print 'D31: kWh per hour, new, daily, non-CPP:', kWhPerHrNewDailyWOCPP
	print 'C31: kWh per hour, new, off-peak, non-CPP:', kWhPerHrNewOffPeakWOCPP
	print 'B31: kWh per hour, new, on-peak, non-CPP:', kWhPerHrNewOnPeakWOCPP
	print 'B33: On-peak change-in-load factor, non-CPP:', prismDRDict['impactFactorOnPeakWOCPP']
	print 'C33: Off-peak change-in-load factor, non-CPP:', prismDRDict['impactFactorOffPeakWOCPP']
	
	
	#CPP days
	kWhPerHrOldOnPeakWCPP = prismDRDict['onPeakWCPPMonAvgkWh']/prismDRDict['hrsOnPeakPerMonthWCPP'] # B14
	kWhPerHrOldOffPeakWCPP = prismDRDict['offPeakWCPPMonAvgkWh']/prismDRDict['hrsOffPeakPerMonthWCPP'] #C14
	logFactorWCPP = math.log(kWhPerHrOldOnPeakWCPP/kWhPerHrOldOffPeakWCPP) + prismDRDict['elasticitySub'] * (math.log(prismDRDict['rateOnPeak']/prismDRDict['rateOffPeak'] - math.log(prismDRDict['rateFlat']/prismDRDict['rateFlat']))) #B12
	kWhPerHrOldDailyWCPP = ((kWhPerHrOldOnPeakWCPP * prismDRDict['numHoursOn']) +
							 (kWhPerHrOldOffPeakWCPP * prismDRDict['numHoursOff']))/24 #D14
	dailyNewPeakWCPP = ((prismDRDict['rateOnPeak'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP) + (prismDRDict['rateOffPeak'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) #D8
	dailyOldPeakWCPP = ((prismDRDict['rateFlat'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP) + (prismDRDict['rateFlat'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) #D7
	kWhPerHrNewDailyWCPP = math.exp(math.log(kWhPerHrOldDailyWCPP) - (prismDRDict['elasticityDaily'] * (math.log(dailyOldPeakWCPP) - math.log(dailyNewPeakWCPP)))) #D15
	kWhPerHrNewOffPeakWCPP =  ((24/float(prismDRDict['numHoursOff'])) * kWhPerHrNewDailyWCPP) / (1+((prismDRDict['numHoursOn']/float(prismDRDict['numHoursOff'])) * math.exp(logFactorWCPP))) #C15
	kWhPerHrNewOnPeakWCPP  = kWhPerHrNewOffPeakWCPP * math.exp(logFactorWCPP) #B15
	kWhDeltaOnPeakWCPP = kWhPerHrNewOnPeakWCPP - kWhPerHrOldOnPeakWCPP #B16
	kWhDeltaOffPeakWCPP = kWhPerHrNewOffPeakWCPP - kWhPerHrOldOffPeakWCPP #C16
	prismDRDict['impactFactorOnPeakWCPP'] = kWhDeltaOnPeakWCPP/kWhPerHrOldOnPeakWCPP #B17
	prismDRDict['impactFactorOffPeakWCPP'] = kWhDeltaOffPeakWCPP/kWhPerHrOldOffPeakWCPP #C17
	
	#PRISM Impacts per Participant
	print 'B14: kWh per hour, old, on-peak, CPP:', kWhPerHrOldOnPeakWCPP
	print 'C14: kWh per hour, old, off-peak, CPP:', kWhPerHrOldOffPeakWCPP
	print 'B12: Log factor, CPP:', logFactorWCPP
	print 'D14: kWh per hour, old, daily, CPP:', kWhPerHrOldDailyWCPP
	print 'D8: New daily on-peak price, CPP:', dailyNewPeakWCPP
	print 'D7: Old daily on-peak price, CPP:', dailyOldPeakWCPP
	print 'D15: kWh per hour, new, daily, CPP:', kWhPerHrNewDailyWCPP
	print 'C15: kWh per hour, new, off-peak, CPP:', kWhPerHrNewOffPeakWCPP
	print 'B15: kWh per hour, new, on-peak, CPP:', kWhPerHrNewOnPeakWCPP
	print 'B17: On-peak change-in-load factor, CPP:', prismDRDict['impactFactorOnPeakWCPP']
	print 'C17: Off-peak change-in-load factor, CPP:', prismDRDict['impactFactorOffPeakWCPP']
	
	
	return prismDRDict



def applyDR(load_profile, rates, schedule, impact_factors):
	modified_load = load_profile
	for idx, load in enumerate(load_profile[schedule['start_index']:schedule['stop_index']+1]):
		print
		if ((idx % 24) < schedule['start_hour']) or ((idx % 24 > schedule['stop_hour'])):
			modified_load[idx + schedule['start_index']] = load * (1 + impact_factors['off_peak'])
		else:
			modified_load[idx + schedule['start_index']] = load * (1 + impact_factors['on_peak'])
	return modified_load
		

def writeCSV(filepath, data):
	outfile = open(filepath, 'wb')
	for row in data:
		outfile.write(str(row) + '\n')
	outfile.close




def _tests():
	prismDRDict = {'elasticitySub':-0.09522,
		'elasticityDaily':-0.02302,
		'startMonth': 5,
		'stopMonth': 9,
		'startHour': 14,
		'stopHour': 18,
		'rateStructure': '2tier', #options: 2tier, 3tier, 2tierCPP
		'rateFlat': 0.20,
		'rateCPP': 1.00,
		'rateOnPeak': 0.40,
		'rateOffPeak': 0.00,
		'numCPPDays': 10
		}
	load_profile = importLoad('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_load.csv')
	prismDRDict['originalLoadProfile'] = load_profile
	#print 'Hour 1 load value:', prismDRDict['originalLoadProfile'][1]
	#print 'Hour 10 load value:', prismDRDict['originalLoadProfile'][10]
	#DEPRECATED: elastcity = importElast('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_elasticity.csv')
	#DEPRICATED: rates = importRates('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_rates.csv')
	#DEPRICATED: schedule = importSchedule('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_schedule.csv')
	prismDRDict = calcTimes(prismDRDict)
	prismDRDict = findCPPDays(prismDRDict)
	prismDRDict = calcEnergy(prismDRDict)
	prismDRDict = calcOffPeak(prismDRDict)
	prismDRDict = calcImpactFactors(prismDRDict)
	#modified_load = applyDR(load_profile, rates, schedule, impact_factors)
	#writeCSV('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_load_modified.csv', modified_load)




if __name__ == '__main__': #Only run if we are calling from the command line, commonly to test functionality
    _tests()