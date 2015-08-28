'''
Created on July 15, 2015
prismDR(xxxxxxx)

Implements the PRISM DR model based on the PRISM model. This model assumes a 2-tier pricing structure (on- and off-peak) with (optionally) critical peak period days.  On these days the on-peak price is typically much higher than non-CPP to encourage a significant reduction in load. The findCPPDays() function identifies these days based on days with the highest load value as found in prismDRInputs['origLoad'].

@author: trevorhardy
'''

import sys
import warnings
import csv
import datetime
import calendar
import math
import operator


def importLoad(file_path):
	load_file = open(file_path, 'r')
	reader = csv.reader(load_file)
	load = list(float(row[0]) for row in reader)
	load_file.close
	return load

def calcTimes(prismDRDict):
    start_date = datetime.date(2009,prismDRDict['startMonth'],1)
    last_day = calendar.monthrange(2009, prismDRDict['stopMonth'])
    stop_date = datetime.date(2009,prismDRDict['stopMonth'],last_day[1])
    day_count = stop_date - start_date
    prismDRDict['dayCount']= day_count.days
    start_index = start_date - datetime.date(2009,1,1)
    prismDRDict['startIndex'] = start_index.days * 24
    prismDRDict['stopIndex'] = prismDRDict['startIndex'] + ((prismDRDict['dayCount']+1) * 24) - 1
    prismDRDict['numMonths'] = prismDRDict['stopMonth'] - prismDRDict['startMonth'] + 1
    prismDRDict['numHoursOn'] = prismDRDict['stopHour'] - prismDRDict['startHour'] + 1
    prismDRDict['numHoursOff'] = (24 - prismDRDict['numHoursOn'])
    if prismDRDict['rateStructure'] == '2tierCPP':
        prismDRDict['hrsOnPeakWCPP'] = prismDRDict['numHoursOn'] * prismDRDict['numCPPDays']
        prismDRDict['hrsOffPeakWCPP'] = prismDRDict['numHoursOff'] * prismDRDict['numCPPDays']
        prismDRDict['hrsOnPeakWOCPP'] = ((prismDRDict['stopHour'] - prismDRDict['startHour']) * prismDRDict['dayCount']) - prismDRDict['hrsOnPeakWCPP']
        prismDRDict['hrsOffPeakWOCPP'] = ((prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeakWOCPP']) - prismDRDict['hrsOffPeakWCPP']
        prismDRDict['hrsOnPeakPerMonthWCPP'] = float(prismDRDict['hrsOnPeakWCPP']) / float(prismDRDict['numMonths'])
        prismDRDict['hrsOffPeakPerMonthWCPP'] = float(prismDRDict['hrsOffPeakWCPP']) / float(prismDRDict['numMonths'])
    else:
        prismDRDict['hrsOnPeakWOCPP'] = ((prismDRDict['stopHour'] - prismDRDict['startHour']) * prismDRDict['dayCount'])
        prismDRDict['hrsOffPeakWOCPP'] = ((prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeakWOCPP'])
    prismDRDict['hrsOnPeakPerMonthWOCPP'] = float(prismDRDict['hrsOnPeakWOCPP']) / float(prismDRDict['numMonths'])
    prismDRDict['hrsOffPeakPerMonthWOCPP'] = float(prismDRDict['hrsOffPeakWOCPP']) / float(prismDRDict['numMonths'])
    return prismDRDict

def findCPPDays(prismDRDict):
    #Finds largest load days and designates them CPP days.
    maxCount = 0
    tempLoad = list(prismDRDict['origLoad'])
    while maxCount < prismDRDict['numCPPDays']:
        maxIndex, maxLoad = max(enumerate(tempLoad), key=operator.itemgetter(1))
        maxIndex = (maxIndex // 24) * 24 #First hour of day.
        tempLoad[maxIndex:maxIndex + 24] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] #Zero-ing out so that we don't consider this day again
        if maxIndex > prismDRDict['startIndex'] & maxIndex < prismDRDict['stopIndex']: #max day was in DR season
            for idx in range(0,24):
                prismDRDict['cppDayIdx'].append(maxIndex + idx)
            maxCount+=1
    return prismDRDict

def calcEnergy(prismDRDict):
    for idx, load in enumerate(prismDRDict['origLoad']):
        if idx > prismDRDict['startIndex'] and idx < prismDRDict['stopIndex']: #is hour of year in the cooling season?
            #print 'Cooling season, idx = ', idx
            hourOfDay  = idx % 24
            if prismDRDict['rateStructure'] == '2tierCPP':
                if idx in prismDRDict['cppDayIdx']:
                    if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                        prismDRDict['offPeakWCPPEnergy'] += load
                    else:
                        prismDRDict['onPeakWCPPEnergy'] += load
                else:
                    if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                        prismDRDict['offPeakWOCPPEnergy'] += load
                    else:
                        prismDRDict['onPeakWOCPPEnergy'] += load
            else:
                if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                    prismDRDict['offPeakWOCPPEnergy'] += load
                else:
                    prismDRDict['onPeakWOCPPEnergy'] += load
        #else: #Load outside of cooling season not used
    if prismDRDict['rateStructure'] == '2tierCPP':
        prismDRDict['totalEnergy'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy'] + prismDRDict['offPeakWCPPEnergy'] + prismDRDict['onPeakWCPPEnergy']
        prismDRDict['onPeakWCPPMonAvgkWh'] = prismDRDict['onPeakWCPPEnergy']/prismDRDict['numMonths']
        prismDRDict['offPeakWCPPMonAvgkWh'] = prismDRDict['offPeakWCPPEnergy']/prismDRDict['numMonths']
    else:
        prismDRDict['totalEnergy'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy']
    prismDRDict['onPeakWOCPPMonAvgkWh'] = prismDRDict['onPeakWOCPPEnergy']/prismDRDict['numMonths']
    prismDRDict['offPeakWOCPPMonAvgkWh'] = prismDRDict['offPeakWOCPPEnergy']/prismDRDict['numMonths']
    prismDRDict['totalMonAvgkWh'] = prismDRDict['totalEnergy']/prismDRDict['numMonths']
    return prismDRDict

def calcOffPeak(prismDRDict):
    original_bill = prismDRDict['rateFlat'] * prismDRDict['totalMonAvgkWh']
    if prismDRDict['rateStructure'] == '2tierCPP':
        prismDRDict['rateOffPeak'] = (original_bill - (prismDRDict['rateCPP']*prismDRDict['onPeakWCPPMonAvgkWh'] + prismDRDict['rateOnPeak']*prismDRDict['onPeakWOCPPMonAvgkWh']))/(prismDRDict['offPeakWCPPMonAvgkWh'] + prismDRDict['offPeakWOCPPMonAvgkWh'])
    else:
        prismDRDict['rateOffPeak'] = (original_bill - (prismDRDict['rateOnPeak']*prismDRDict['onPeakWOCPPMonAvgkWh']))/(prismDRDict['offPeakWOCPPMonAvgkWh'])
    if prismDRDict['rateOffPeak'] < 0:
        print 'ERROR: Off-peak rate is negative :', prismDRDict['rateOffPeak']
    return prismDRDict

def calcImpactFactors(prismDRDict):
	#Non-CPP days
    kWhPerHrOldOnPeakWOCPP = prismDRDict['onPeakWOCPPMonAvgkWh']/prismDRDict['hrsOnPeakPerMonthWOCPP'] # B30
    kWhPerHrOldOffPeakWOCPP = prismDRDict['offPeakWOCPPMonAvgkWh']/prismDRDict['hrsOffPeakPerMonthWOCPP'] #C30
    logFactorWOCPP = math.log(kWhPerHrOldOnPeakWOCPP/kWhPerHrOldOffPeakWOCPP) + prismDRDict['elasticitySubWOCPP'] * (math.log(prismDRDict['rateOnPeak']/prismDRDict['rateOffPeak'] - math.log(prismDRDict['rateFlat']/prismDRDict['rateFlat']))) #B28
    kWhPerHrOldDailyWOCPP = ((kWhPerHrOldOnPeakWOCPP * prismDRDict['numHoursOn']) +
							  (kWhPerHrOldOffPeakWOCPP * prismDRDict['numHoursOff']))/24 #D30
    dailyNewPeakWOCPP = ((prismDRDict['rateOnPeak'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP) + (prismDRDict['rateOffPeak'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D24
    dailyOldPeakWOCPP = ((prismDRDict['rateFlat'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP) + (prismDRDict['rateFlat'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D23
    kWhPerHrNewDailyWOCPP = math.exp(math.log(kWhPerHrOldDailyWOCPP) - (prismDRDict['elasticityDailyWOCPP'] * (math.log(dailyOldPeakWOCPP) - math.log(dailyNewPeakWOCPP)))) #D31
    kWhPerHrNewOffPeakWOCPP =  ((24/float(prismDRDict['numHoursOff'])) * kWhPerHrNewDailyWOCPP) / (1+((prismDRDict['numHoursOn']/float(prismDRDict['numHoursOff'])) * math.exp(logFactorWOCPP))) #C31
    kWhPerHrNewOnPeakWOCPP  = kWhPerHrNewOffPeakWOCPP * math.exp(logFactorWOCPP) #B31
    kWhDeltaOnPeakWOCPP = kWhPerHrNewOnPeakWOCPP - kWhPerHrOldOnPeakWOCPP #B32
    kWhDeltaOffPeakWOCPP = kWhPerHrNewOffPeakWOCPP - kWhPerHrOldOffPeakWOCPP #C32
    prismDRDict['impactFactorOnPeakWOCPP'] = kWhDeltaOnPeakWOCPP/kWhPerHrOldOnPeakWOCPP #B33
    prismDRDict['impactFactorOffPeakWOCPP'] = kWhDeltaOffPeakWOCPP/kWhPerHrOldOffPeakWOCPP #C33	
	#CPP days
    if prismDRDict['rateStructure'] == '2tierCPP':
        kWhPerHrOldOnPeakWCPP = prismDRDict['onPeakWCPPMonAvgkWh']/prismDRDict['hrsOnPeakPerMonthWCPP'] # B14
        kWhPerHrOldOffPeakWCPP = prismDRDict['offPeakWCPPMonAvgkWh']/prismDRDict['hrsOffPeakPerMonthWCPP'] #C14
        logFactorWCPP = math.log(kWhPerHrOldOnPeakWCPP/kWhPerHrOldOffPeakWCPP) + prismDRDict['elasticitySubWCPP'] * (math.log(prismDRDict['rateCPP']/prismDRDict['rateOffPeak'] - math.log(prismDRDict['rateFlat']/prismDRDict['rateFlat']))) #B12
        kWhPerHrOldDailyWCPP = ((kWhPerHrOldOnPeakWCPP * prismDRDict['numHoursOn']) +
                                 (kWhPerHrOldOffPeakWCPP * prismDRDict['numHoursOff']))/24 #D14
        dailyNewPeakWCPP = ((prismDRDict['rateCPP'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP) + (prismDRDict['rateOffPeak'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) #D8
        dailyOldPeakWCPP = ((prismDRDict['rateFlat'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP) + (prismDRDict['rateFlat'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWCPP)) #D7
        kWhPerHrNewDailyWCPP = math.exp(math.log(kWhPerHrOldDailyWCPP) - (prismDRDict['elasticityDailyWCPP'] * (math.log(dailyOldPeakWCPP) - math.log(dailyNewPeakWCPP)))) #D15
        kWhPerHrNewOffPeakWCPP =  ((24/float(prismDRDict['numHoursOff'])) * kWhPerHrNewDailyWCPP) / (1+((prismDRDict['numHoursOn']/float(prismDRDict['numHoursOff'])) * math.exp(logFactorWCPP))) #C15
        kWhPerHrNewOnPeakWCPP  = kWhPerHrNewOffPeakWCPP * math.exp(logFactorWCPP) #B15
        kWhDeltaOnPeakWCPP = kWhPerHrNewOnPeakWCPP - kWhPerHrOldOnPeakWCPP #B16
        kWhDeltaOffPeakWCPP = kWhPerHrNewOffPeakWCPP - kWhPerHrOldOffPeakWCPP #C16
        prismDRDict['impactFactorOnPeakWCPP'] = kWhDeltaOnPeakWCPP/kWhPerHrOldOnPeakWCPP #B17
        prismDRDict['impactFactorOffPeakWCPP'] = kWhDeltaOffPeakWCPP/kWhPerHrOldOffPeakWCPP #C17
    return prismDRDict

def applyDR(prismDRDict):
    prismDRDict['modLoad'] = list(prismDRDict['origLoad'])
    for idx, load in enumerate(prismDRDict['origLoad']):
        if idx > prismDRDict['startIndex'] and idx < prismDRDict['stopIndex']: #is hour of year in the cooling season?
            #print 'Cooling season, idx = ', idx
            hourOfDay  = idx % 24
            if prismDRDict['rateStructure'] == '2tierCPP':
                if idx in prismDRDict['cppDayIdx']:
                    if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWCPP'])
                    else:
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWCPP'])
                else:
                    if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWOCPP'])
                    else:
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWOCPP'])
            else:
                if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWOCPP'])
                else:
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWOCPP'])
        #else: #Load outside of cooling season not modified
    return prismDRDict

def writeCSV(filepath, data):
	outfile = open(filepath, 'wb')
	for row in data:
		outfile.write(str(row) + '\n')
	outfile.close

def initPRISMDRDict(prismDRDict):
    prismDRDict['origLoad'] = list()
    prismDRDict['rateOffPeak']= 0.0
    prismDRDict['dayCount']= 0.0
    prismDRDict['startIndex'] = 0.0
    prismDRDict['stopIndex'] = 0.0
    prismDRDict['numMonths'] = 0.0
    prismDRDict['numHoursOn'] = 0.0
    prismDRDict['numHoursOff'] = 0.0
    prismDRDict['hrsOnPeakWOCPP'] = 0.0
    prismDRDict['hrsOffPeakWOCPP'] = 0.0
    prismDRDict['hrsOnPeakPerMonthWOCPP'] = 0.0
    prismDRDict['hrsOffPeakPerMonthWOCPP'] = 0.0
    prismDRDict['onPeakWOCPPEnergy'] = 0.0
    prismDRDict['offPeakWOCPPEnergy'] = 0.0
    prismDRDict['impactFactorOnPeakWOCPP'] = 0.0
    prismDRDict['impactFactorOffPeakWOCPP'] = 0.0
    prismDRDict['modLoad'] = list()
    if prismDRDict['rateStructure'] == '2tierCPP':
        prismDRDict['hrsOnPeakWCPP'] = 0.0
        prismDRDict['hrsOffPeakWCPP'] = 0.0
        prismDRDict['offPeakWCPPEnergy'] = 0.0
        prismDRDict['onPeakWCPPEnergy'] = 0.0
        prismDRDict['hrsOnPeakPerMonthWCPP'] = 0.0
        prismDRDict['hrsOffPeakPerMonthWCPP'] = 0.0
        prismDRDict['impactFactorOnPeakWCPP'] = 0.0
        prismDRDict['impactFactorOffPeakWCPP'] = 0.0
        prismDRDict['cppDayIdx'] = []
    return prismDRDict

def _tests():
    prismDRInputs = {
        'rateStructure': '2tierCPP', #options: 2tier, 2tierCPP
        'elasticitySubWOCPP':-0.09522,
        'elasticityDailyWOCPP':-0.02302,
        'elasticitySubWCPP':-0.09698, #Only required for 2tierCPP
        'elasticityDailyWCPP':-0.01607, #Only reuquired for 2tierCPP
        'startMonth': 5,
        'stopMonth': 9,
        'startHour': 14,
        'stopHour': 18,
        'rateFlat': 0.15,
        'rateCPP': 2.80, #Only required for 2tierCPP
        'rateOnPeak': 0.30,
        'numCPPDays': 10, #Only required for 2tierCPP
		}
    prismDRDict = initPRISMDRDict(prismDRInputs)
    prismDRDict['origLoad'] = importLoad('./test_load.csv')
    prismDRDict = calcTimes(prismDRDict)
    if prismDRDict['rateStructure'] == '2tierCPP':
        prismDRDict = findCPPDays(prismDRDict)
    prismDRDict = calcEnergy(prismDRDict)
    prismDRDict = calcOffPeak(prismDRDict)
    prismDRDict = calcImpactFactors(prismDRDict)
    prismDRDict = applyDR(prismDRDict)
    writeCSV('./test_load_modified.csv', prismDRDict['modLoad'])

if __name__ == '__main__': #Only run if we are calling from the command line, commonly to test functionality
    _tests()


'''
Other documentation.

    
    
    Input:    prismDRInputs = {
    'rateStructure': '2tierCPP', options: 2tier, 2tierCPP
    'elasticitySubWOCPP': Substitution elasticty during non-CPP days.
    'elasticityDailyWOCPP': Daily elasticity during non-CPP days.
    'elasticitySubWCPP':, Substitution elasticty during CPP days. Only required for 2tierCPP
    'elasticityDailyWCPP':, Daily elasticity during non-CPP days. Only reuquired for 2tierCPP
    'startMonth': 1-12. Beginning month of the cooling season when the DR program will run.
    'stopMonth': 1-12. Ending month of the cooling season when the DR program will run.
    'startHour': 0-23. Beginning hour for on-peak and CPP rates.
    'stopHour': 0-23. Ending hour for on-peak and CPP rates.
    'rateFlat': pre-DR Time-independent rate paid by residential consumers.
    'rateCPP':  Peak hour rate on CPP days. Only required for 2tierCPP
    'rateOnPeak': Peak hour rate on non-CPP days.
    'numCPPDays': Number of CPP days in a cooling season. Only required for 2tierCPP
    'origLoad': 8760 load value that will be modified by the DR program.
    }
    Output:
        prismDRDict = {
        (All prismDRInputs)
        prismDRDict['modLoad']: DR-modified load.
        prismDRDict['dayCount']: Number of days in the cooling season
        prismDRDict['startIndex']: Hour number (first hour = 0) of the first hour of the first day of the cooling season
        prismDRDict['stopIndex']: Hour number (first hour = 0) of the last hour of the last day of the cooling season
        prismDRDict['numMonths']: Number of months in cooling season
        prismDRDict['numHoursOn']: Number of hours on-peak each day
        prismDRDict['numHoursOff']: Number of hours off-peak each day
        prismDRDict['hrsOnPeakWOCPP']: Total number of hours on-peak on non-CPP days during cooling season.
        prismDRDict['hrsOffPeakWOCPP']: Total number of hours off-peak on non-CPP days during cooling season.
        prismDRDict['hrsOnPeakPerMonthWOCPP']: Average number of hours on-peak per month (excluding CPP hours).
        prismDRDict['hrsOffPeakPerMonthWOCPP']: Average number of hours off-peak per month (excluding CPP hours).
        prismDRDict['onPeakWOCPPEnergy']: Total energy during on-peak hours during non-CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
        prismDRDict['offPeakWOCPPEnergy']: Total energy during off-peak hours during non-CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
        prismDRDict['impactFactorOnPeakWOCPP'] = Change in load factor due to residential air-conditioner response due to DR program for on-peak, non-CPP hours during cooling season.
        prismDRDict['impactFactorOffPeakWOCPP'] = Change in load factor due to residential air-conditioner response due to DR program for off-peak, non-CPP hours during cooling season.
        prismDRDict['hrsOnPeakWCPP']: Total number of hours on-peak on CPP days during cooling season.
        prismDRDict['hrsOffPeakWCPP']: Total number of hours off-peak on CPP days during cooling season.
        prismDRDict['offPeakWCPPEnergy']: Total energy during off-peak hours during CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
        prismDRDict['onPeakWCPPEnergy'] : Total energy during on-peak hours during CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
        prismDRDict['hrsOnPeakPerMonthWCPP']: Average number of CPP hours per month.
        prismDRDict['hrsOffPeakPerMonthWCPP']: Average number of hours off-peak per month on CPP days.
        prismDRDict['impactFactorOnPeakWCPP']: Change in load factor due to residential air-conditioner response due to DR program for on-peak, CPP hours during cooling season.
        prismDRDict['impactFactorOffPeakWCPP']: Change in load factor due to residential air-conditioner response due to DR program for off-peak, CPP hours during cooling season.
        
        }
    Example:
    'rateStructure': '2tierCPP', #options: 2tier, 2tierCPP
    'elasticitySubWOCPP':-0.09522,
    'elasticityDailyWOCPP':-0.02302,
    'elasticitySubWCPP':-0.09698, #Only required for 2tierCPP
    'elasticityDailyWCPP':-0.01607, #Only reuquired for 2tierCPP
    'startMonth': 5,
    'stopMonth': 9,
    'startHour': 14,
    'stopHour': 18,
    'rateFlat': 0.15,
    'rateCPP': 2.80, #Only required for 2tierCPP
    'rateOnPeak': 0.30,
    'numCPPDays': 10, #Only required for 2tierCPP
'''