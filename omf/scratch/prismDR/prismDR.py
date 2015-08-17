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
	prismDRDict['hrsOnPeak'] = (prismDRDict['stopHour'] - prismDRDict['startHour']) * prismDRDict['dayCount']
	prismDRDict['hrsOffPeak'] = (prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeak']
	prismDRDict['numMonths'] = prismDRDict['stopMonth'] - prismDRDict['startMonth'] + 1
	prismDRDict['numHoursOn'] = prismDRDict['stopHour'] - prismDRDict['startHour'] + 1
	prismDRDict['numHoursOff'] = (24 - prismDRDict['numHoursOn'])
	prismDRDict['hrsOnPeakPerMonth'] = float(prismDRDict['hrsOnPeak']) / float(prismDRDict['numMonths'])
	prismDRDict['hrsOffPeakPerMonth'] = float(prismDRDict['hrsOffPeak']) / float(prismDRDict['numMonths'])
	print 'Start index:', prismDRDict['startIndex']
	print 'Stop index:', prismDRDict['stopIndex']
	print 'On-peak hours per day:', prismDRDict['numHoursOn']
	print 'Off-peak hours per day:', prismDRDict['numHoursOff']
	print 'Total hour on-peak:', prismDRDict['hrsOnPeak']					#PRISM Impacts Inputs C51 (enter this value there)
	print 'Total hours off-peak:', prismDRDict['hrsOffPeak']					#PRISM Impacts Inputs C52 (enter this value there)
	print 'Number of months in cooling season:', prismDRDict['numMonths']
	print 'Hours on-peak per month:', prismDRDict['hrsOnPeakPerMonth']		#PRISM Impacts Inputs D51
	print 'Hours off-peak per month:', prismDRDict['hrsOffPeakPerMonth']	#PRISM Impacts Inputs D52
	return prismDRDict

def findCPPDays(prismDRDict):
	#Finds largest load days and designates them CPP days.
	maxCount = 0
	tempLoad = prismDRDict['originalLoadProfile']
	prismDRDict['cppDayIdx'] = []
	while maxCount < prismDRDict['numCPPDays']:
		maxIndex, maxLoad = max(enumerate(tempLoad), key=operator.itemgetter(1))
		#print 'Peak load index', maxIndex
		maxIndex = (maxIndex // 24) * 24 #First hour of day.
		#print 'Peak load start of day', maxIndex
		tempLoad[maxIndex:maxIndex + 23] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] #Zero-ing out so that we don't consider this day again
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
	#This needs to be reworked
	for idx, load in enumerate(prismDRDict['originalLoadProfile'][startIndex:stopIndex+1]):
		if idx in prismDRDict['cppDayIdx']:
			if ((idx % 24) < schedule['startHour']) or ((idx % 24 > prismDRDict['stopHour'])):
				prismDRDict['offPeakWOCPPEnergy'] += load
			else:
				prismDRDict['onPeakWOCPPEnergy'] += load
			prismDRDict['totalWOCPP'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy']
		else:
			if ((idx % 24) < schedule['startHour']) or ((idx % 24 > prismDRDict['stopHour'])):
				prismDRDict['offPeakWCPPEnergy'] += load
			else:
				prismDRDict['onPeakWCPPEnergy'] += load
			prismDRDict['totalWCPP'] = prismDRDict['offPeakWCPPEnergy'] + prismDRDict['onPeakWCPPEnergy']
	#print 'On-peak energy:', energyProfile['on_peak']		#PRISM Impacts Inputs B13 (enter this value there)
	#print 'Off-peak energy:', energyProfile['off_peak']	#PRISM Impacts Inputs B14 (enter this value there)
	#print 'Total energy:', energyProfile['total']			#PRISM Impacts Inputs B15
	return prismDRDict

def calcOffPeak(rates, energyProfile):
	original_bill = rates['flat'] * energyProfile['total']
	rates['off_peak'] = (original_bill - (rates['on_peak'] * energyProfile['on_peak']))/energyProfile['off_peak']
	return rates

def calcImpactFactors(rates, schedule, elastcity, energyProfile):
	impact_factors = dict()
	kWh_per_hr_old_on_peak = energyProfile['on_peak']/schedule['hrs_on_peak_per_month']
	kWh_per_hr_old_off_peak = energyProfile['off_peak']/schedule['hrs_off_peak_per_month']
	log_factor = math.log(kWh_per_hr_old_on_peak/kWh_per_hr_old_off_peak) + elastcity['sub']*   \
								(math.log(rates['on_peak']/rates['off_peak']) - math.log(rates['flat']/rates['flat']))
	kWh_per_hr_old_daily = ((kWh_per_hr_old_on_peak * schedule['num_hours_on']) +
								(kWh_per_hr_old_off_peak * schedule['num_hours_off']))/24
	rates['daily_new_peak'] = ((rates['on_peak'] * schedule['num_hours_on'] * kWh_per_hr_old_on_peak) +  \
								(rates['off_peak'] * schedule['num_hours_off'] * kWh_per_hr_old_off_peak))/  \
								((schedule['num_hours_on']*kWh_per_hr_old_on_peak)+(schedule['num_hours_off']*kWh_per_hr_old_off_peak))
	rates['daily_old_peak'] = ((rates['flat'] * schedule['num_hours_on'] * kWh_per_hr_old_on_peak) +  \
								(rates['flat'] * schedule['num_hours_off'] * kWh_per_hr_old_off_peak))/  \
								((schedule['num_hours_on']*kWh_per_hr_old_on_peak)+(schedule['num_hours_off']*kWh_per_hr_old_off_peak))
	kWh_per_hr_new_daily = math.exp(math.log(kWh_per_hr_old_daily) -  \
								(elastcity['daily'] * (math.log(rates['daily_old_peak']) - math.log(rates['daily_new_peak']))))
	kWh_per_hr_new_off_peak = ((24/float(schedule['num_hours_off'])) * kWh_per_hr_new_daily)/ \
								(1+((schedule['num_hours_on']/float(schedule['num_hours_off'])) * math.exp(log_factor)))
	kWh_per_hr_new_on_peak = kWh_per_hr_new_off_peak  * math.exp(log_factor)
	kWh_delta_on_peak = kWh_per_hr_new_on_peak - kWh_per_hr_old_on_peak
	kWh_delta_off_peak = kWh_per_hr_new_off_peak - kWh_per_hr_old_off_peak
	impact_factors['on_peak'] = kWh_delta_on_peak/kWh_per_hr_old_on_peak
	impact_factors['off_peak'] = kWh_delta_off_peak/kWh_per_hr_old_off_peak
	#print 'kWh per hour, old, on-peak:', kWh_per_hr_old_on_peak				#PRISM Impacts per Participant B30
	#print 'kWh per hour, old, off-peak:', kWh_per_hr_old_off_peak			#PRISM Impacts per Participant C30
	#print 'Log factor:', log_factor										#PRISM Impacts per Participant B28
	#print 'kWh per hour, old, daily', kWh_per_hr_old_daily					#PRISM Impacts per Participant D30
	#print 'New daily on-peak price:', rates['daily_new_peak']				#PRISM Impacts per Participant D24
	#print 'Old daily on-peak price:', rates['daily_old_peak']				#PRISM Impacts per Participant D23
	#print 'kWh per hour, new, daily:', kWh_per_hr_new_daily					#PRISM Impacts per Participant D31
	#print 'kWh per hour, new, off-peak:', kWh_per_hr_new_off_peak					#PRISM Impacts per Participant C31
	#print 'kWh per hour, new, on-peak', kWh_per_hr_new_on_peak				#PRISM Impacts per Participant B31
	#print 'On-peak change-in-load factor:', impact_factors['on_peak']		#PRISM Impacts per Participant B33
	#print 'Off-peak change-in-load factor:', impact_factors['off_peak']		#PRISM Impacts per Participant B34
	return impact_factors



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
		'offPeakRate': 0.1,
		'onPeakRate': 0.3,
		'cppRate': 1.0,
		'startMonth': 5,
		'stopMonth': 9,
		'startHour': 14,
		'stopHour': 18,
		'rateStructure': '2tier', #options: 2tier, 3 tier, 2tierCPP
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
	#prismDRDict = calcEnergy(prismDRDict)
	#rates = calcOffPeak(rates, energyProfile)
	#impact_factors = calcImpactFactors(rates, schedule, elastcity, energyProfile)
	#modified_load = applyDR(load_profile, rates, schedule, impact_factors)
	#writeCSV('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_load_modified.csv', modified_load)




if __name__ == '__main__': #Only run if we are calling from the command line, commonly to test functionality
    _tests()