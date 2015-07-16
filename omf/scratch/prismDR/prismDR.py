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

#def findOffPeakRate():

#def calcLoadImpacts():

def importLoad(file_path):
	load_file = open(file_path, 'r')
	reader = csv.reader(load_file)
	load = list(float(row[0]) for row in reader)
	load_file.close
	return load

def importElast(file_path):
	elast = dict()
	elast_file = open(file_path, 'rU')
	reader = csv.reader(elast_file)
	temp = list(float(row[0]) for row in reader)
	elast['sub'] = temp[0]
	elast['daily'] = temp[1]
	elast_file.close
	return elast

def importRates(file_path):
	rates = dict()
	rate_file = open(file_path, 'rU')
	reader = csv.reader(rate_file)
	temp = list(float(row[0]) for row in reader)
	rates['flat'] = temp[0]
	rates['on_peak'] = temp[1]
	rate_file.close
	return rates

def importSchedule(file_path):
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

def calcTimes(schedule):
	start_date = datetime.date(2009,schedule['start_month'],1)
	last_day =calendar.monthrange(2009, schedule['stop_month'])
	stop_date = datetime.date(2009,schedule['stop_month'],last_day[1])
	day_count = stop_date - start_date
	schedule['day_count']= day_count.days
	start_index = start_date - datetime.date(2009,1,1)
	schedule['start_index'] = start_index.days * 24
	schedule['stop_index'] = schedule['start_index'] + ((schedule['day_count']+1) * 24) - 1
	schedule['hrs_on_peak'] = (schedule['stop_hour'] - schedule['start_hour']) * schedule['day_count']
	schedule['hrs_off_peak'] = (schedule['day_count'] * 24) - schedule['hrs_on_peak']
	schedule['num_months'] = schedule['stop_month']-schedule['start_month'] + 1
	schedule['num_hours_on'] = schedule['stop_hour']-schedule['start_hour'] + 1
	schedule['num_hours_off'] = (24 - schedule['num_hours_on'])
	schedule['hrs_on_peak_per_month'] = float(schedule['hrs_on_peak']) / float(schedule['num_months'])
	schedule['hrs_off_peak_per_month'] = float(schedule['hrs_off_peak']) / float(schedule['num_months'])
	#print 'Start index:', schedule['start_index']
	#print 'On-peak hours per day:', schedule['num_hours_on']
	#print 'Off-peak hours per day:', schedule['num_hours_off']
	#print 'Total hour on-peak:', schedule['hrs_on_peak']						#PRISM Impacts Inputs C51 (enter this value there)
	#print 'Total hours off-peak:', schedule['hrs_off_peak']					#PRISM Impacts Inputs C52 (enter this value there)
	#print 'Number of months in cooling season:', schedule['num_months']
	#print 'Hours on-peak per month:', schedule['hrs_on_peak_per_month']		#PRISM Impacts Inputs D51
	#print 'Hours off-peak per month:', schedule['hrs_off_peak_per_month']		#PRISM Impacts Inputs D52
	return schedule

def calcEnergy(energyProfile, schedule, load_profile):
	for idx, load in enumerate(load_profile[schedule['start_index']:schedule['stop_index']+1]):
		if ((idx % 24) < schedule['start_hour']) or ((idx % 24 > schedule['stop_hour'])):
			energyProfile['off_peak'] += load
		else:
			energyProfile['on_peak'] += load
		energyProfile['total'] = energyProfile['off_peak'] + energyProfile['on_peak']
	#print 'On-peak energy:', energyProfile['on_peak']		#PRISM Impacts Inputs B13 (enter this value there)
	#print 'Off-peak energy:', energyProfile['off_peak']	#PRISM Impacts Inputs B14 (enter this value there)
	#print 'Total energy:', energyProfile['total']			#PRISM Impacts Inputs B15
	return energyProfile

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
			load_profile = importLoad('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_load.csv')
			elastcity = importElast('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_elasticity.csv')
			rates = importRates('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_rates.csv')
			schedule = importSchedule('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_schedule.csv')
			schdeule = calcTimes(schedule)
			energyProfile = dict()
			energyProfile['off_peak'] = 0
			energyProfile['on_peak'] = 0
			energyProfile = calcEnergy(energyProfile, schedule, load_profile)
			rates = calcOffPeak(rates, energyProfile)
			impact_factors = calcImpactFactors(rates, schedule, elastcity, energyProfile)
			modified_load = applyDR(load_profile, rates, schedule, impact_factors)
			writeCSV('/Users/hard312/Gridlab-D/omf/omf/scratch/prismDR/test_load_mofidifed.csv', modified_load)




if __name__ == '__main__': #Only run if we are calling from the command line, commonly to test functionality
    _tests()