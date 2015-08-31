'''
Implements the PRISM DR model based on the PRISM model. This model assumes a 2-tier pricing structure (on- and off-peak) with (optionally) critical peak period days.  On these days the on-peak price is typically much higher than non-CPP to encourage a significant reduction in load.

See _tests() for inputs.

prism() output dictionary:
{
	..., # All prismDRInputs included in output dict.
	'modLoad': ..., # DR-modified load.
	'dayCount': ..., # Number of days in the cooling season
	'startIndex': ..., # Hour number (first hour = 0) of the first hour of the first day of the cooling season
	'stopIndex': ..., # Hour number (first hour = 0) of the last hour of the last day of the cooling season
	'numMonths': ..., # Number of months in cooling season
	'numHoursOn': ..., # Number of hours on-peak each day
	'numHoursOff': ..., # Number of hours off-peak each day
	'hrsOnPeakWOCPP': ..., # Total number of hours on-peak on non-CPP days during cooling season.
	'hrsOffPeakWOCPP': ..., # Total number of hours off-peak on non-CPP days during cooling season.
	'hrsOnPeakPerMonthWOCPP': ..., # Average number of hours on-peak per month (excluding CPP hours).
	'hrsOffPeakPerMonthWOCPP': ..., # Average number of hours off-peak per month (excluding CPP hours).
	'onPeakWOCPPEnergy': ..., # Total energy during on-peak hours during non-CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
	'offPeakWOCPPEnergy': ..., # Total energy during off-peak hours during non-CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
	'impactFactorOnPeakWOCPP':..., # Change in load factor due to residential air-conditioner response due to DR program for on-peak, non-CPP hours during cooling season.
	'impactFactorOffPeakWOCPP': # Change in load factor due to residential air-conditioner response due to DR program for off-peak, non-CPP hours during cooling season.
	'hrsOnPeakWCPP': ..., # Total number of hours on-peak on CPP days during cooling season.
	'hrsOffPeakWCPP': ..., # Total number of hours off-peak on CPP days during cooling season.
	'offPeakWCPPEnergy': ..., # Total energy during off-peak hours during CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
	'onPeakWCPPEnergy'] : Total energy during on-peak hours during CPP days during the cooling season. Units are the energy equivalent of that in the 'origLoad' value.
	'hrsOnPeakPerMonthWCPP': ..., # Average number of CPP hours per month.
	'hrsOffPeakPerMonthWCPP': ..., # Average number of hours off-peak per month on CPP days.
	'impactFactorOnPeakWCPP': ..., # Change in load factor due to residential air-conditioner response due to DR program for on-peak, CPP hours during cooling season.
	'impactFactorOffPeakWCPP': ..., # Change in load factor due to residential air-conditioner response due to DR program for off-peak, CPP hours during cooling season.
}

Created on July 15, 2015
@author: trevorhardy
'''

import datetime
import calendar
import math
import operator

def prism(prismDRDict):
    ''' Calculate demand changes based on Brattle's PRISM. '''
    # Calculate times.
    start_date = datetime.date(2009,prismDRDict['startMonth'],1)
    last_day = calendar.monthrange(2009, prismDRDict['stopMonth'])
    stop_date = datetime.date(2009,prismDRDict['stopMonth'],last_day[1])
    day_count = stop_date - start_date
    prismDRDict['dayCount']= day_count.days
    start_index = start_date - datetime.date(2009,1,1)
    prismDRDict['startIndex'] = start_index.days * 24
    prismDRDict['stopIndex'] = prismDRDict['startIndex'] + ((prismDRDict['dayCount']+1) * 24) - 1
    prismDRDict['numMonths'] = prismDRDict['stopMonth'] - prismDRDict['startMonth'] + 1
    if prismDRDict['rateStructure'] == '3tier':
        prismDRDict['numHours3Tier'] = prismDRDict['stop3TierHour'] - prismDRDict['start3TierHour'] + 1
        prismDRDict['numHoursOn'] = prismDRDict['stopHour'] - prismDRDict['startHour'] + 1 - prismDRDict['numHours3Tier']
        prismDRDict['numHoursOff'] = (24 - prismDRDict['numHoursOn'] - prismDRDict['numHours3Tier'])
    else:
        prismDRDict['numHoursOn'] = prismDRDict['stopHour'] - prismDRDict['startHour'] + 1
        prismDRDict['numHoursOff'] = (24 - prismDRDict['numHoursOn'])
    if prismDRDict['rateStructure'] == '2tierCPP'  or prismDRDict['rateStructure'] == 'PTR':
        prismDRDict['hrsOnPeakWCPP'] = prismDRDict['numHoursOn'] * prismDRDict['numCPPDays']
        prismDRDict['hrsOffPeakWCPP'] = prismDRDict['numHoursOff'] * prismDRDict['numCPPDays']
        prismDRDict['hrsOnPeakWOCPP'] = ((prismDRDict['stopHour'] - prismDRDict['startHour'] + 1) * prismDRDict['dayCount']) - prismDRDict['hrsOnPeakWCPP']
        prismDRDict['hrsOffPeakWOCPP'] = ((prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeakWOCPP']) - prismDRDict['hrsOffPeakWCPP']
        prismDRDict['hrsOnPeakPerMonthWCPP'] = float(prismDRDict['hrsOnPeakWCPP']) / float(prismDRDict['numMonths'])
        prismDRDict['hrsOffPeakPerMonthWCPP'] = float(prismDRDict['hrsOffPeakWCPP']) / float(prismDRDict['numMonths'])
    if prismDRDict['rateStructure'] == '3tier':
        prismDRDict['hrsOn3TierPeak'] = ((prismDRDict['stop3TierHour'] - prismDRDict['start3TierHour'] + 1) * prismDRDict['dayCount'])
        prismDRDict['hrsOnPeakWOCPP'] = ((prismDRDict['stopHour'] - prismDRDict['startHour']) * prismDRDict['dayCount']) - prismDRDict['hrsOn3TierPeak']
        prismDRDict['hrsOffPeakWOCPP'] = ((prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeakWOCPP']) - prismDRDict['hrsOn3TierPeak']
#        print prismDRDict['hrsOn3TierPeak']
#        print prismDRDict['hrsOnPeakWOCPP']
#        print prismDRDict['hrsOffPeakWOCPP']
    else:
        prismDRDict['hrsOnPeakWOCPP'] = ((prismDRDict['stopHour'] - prismDRDict['startHour']) * prismDRDict['dayCount'])
        prismDRDict['hrsOffPeakWOCPP'] = ((prismDRDict['dayCount'] * 24) - prismDRDict['hrsOnPeakWOCPP'])
    prismDRDict['hrsOnPeakPerMonthWOCPP'] = float(prismDRDict['hrsOnPeakWOCPP']) / float(prismDRDict['numMonths'])
    prismDRDict['hrsOffPeakPerMonthWOCPP'] = float(prismDRDict['hrsOffPeakWOCPP']) / float(prismDRDict['numMonths'])
    # Do 2tierCPP. Finds largest load days and designates them CPP days.
    if prismDRDict['rateStructure'] == '2tierCPP' or prismDRDict['rateStructure'] == 'PTR':
        prismDRDict['cppDayIdx'] = []
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
    # Calculate energy.
    prismDRDict['onPeakWOCPPEnergy'] = 0.0
    prismDRDict['on3TierPeakEnergy'] = 0.0
    prismDRDict['offPeakWCPPEnergy'] = 0.0
    prismDRDict['offPeakWOCPPEnergy'] = 0.0
    prismDRDict['impactFactorOnPeakWOCPP'] = 0.0
    prismDRDict['impactFactorOn3TeirPeak'] = 0.0
    prismDRDict['impactFactorOffPeakWOCPP'] = 0.0
    prismDRDict['onPeakWCPPEnergy'] = 0.0
    for idx, load in enumerate(prismDRDict['origLoad']):
        if idx > prismDRDict['startIndex'] and idx < prismDRDict['stopIndex']: #is hour of year in the cooling season?
            hourOfDay = idx % 24
            if prismDRDict['rateStructure'] == '2tierCPP' or prismDRDict['rateStructure'] == 'PTR':
                if idx in prismDRDict['cppDayIdx']:
                    if (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                        prismDRDict['onPeakWCPPEnergy'] += load
                    else:
                        prismDRDict['offPeakWCPPEnergy'] += load
                else:
                    if (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                        prismDRDict['onPeakWCPPEnergy'] += load
                    else:
                        prismDRDict['offPeakWCPPEnergy'] += load
            elif prismDRDict['rateStructure'] == '3tier':
                if (hourOfDay >=  prismDRDict['start3TierHour']) and (hourOfDay <= prismDRDict['stop3TierHour']):
                    prismDRDict['on3TierPeakEnergy'] += load
                elif (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                    prismDRDict['onPeakWOCPPEnergy'] += load
                else:
                    prismDRDict['offPeakWOCPPEnergy'] += load
            else:
                if (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                    prismDRDict['onPeakWCPPEnergy'] += load
                else:
                    prismDRDict['offPeakWCPPEnergy'] += load
#    print prismDRDict['on3TierPeakEnergy']
#    print prismDRDict['onPeakWOCPPEnergy']
#    print prismDRDict['offPeakWOCPPEnergy']
        # else: #Load outside of cooling season not used
    if prismDRDict['rateStructure'] == '2tierCPP' or prismDRDict['rateStructure'] == 'PTR':
        prismDRDict['totalEnergy'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy'] + prismDRDict['offPeakWCPPEnergy'] + prismDRDict['onPeakWCPPEnergy']
        prismDRDict['onPeakWCPPMonAvgkWh'] = prismDRDict['onPeakWCPPEnergy']/prismDRDict['numMonths']
        prismDRDict['offPeakWCPPMonAvgkWh'] = prismDRDict['offPeakWCPPEnergy']/prismDRDict['numMonths']
    elif prismDRDict['rateStructure'] == '3tier':
        prismDRDict['totalEnergy'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy'] + prismDRDict['on3TierPeakEnergy']
        prismDRDict['on3TierPeakMonAvgkWh'] = prismDRDict['on3TierPeakEnergy']/prismDRDict['numMonths']
    else:
        prismDRDict['totalEnergy'] = prismDRDict['offPeakWOCPPEnergy'] + prismDRDict['onPeakWOCPPEnergy']
    prismDRDict['onPeakWOCPPMonAvgkWh'] = prismDRDict['onPeakWOCPPEnergy']/prismDRDict['numMonths']
    prismDRDict['offPeakWOCPPMonAvgkWh'] = prismDRDict['offPeakWOCPPEnergy']/prismDRDict['numMonths']
    prismDRDict['totalMonAvgkWh'] = prismDRDict['totalEnergy']/prismDRDict['numMonths']
#    print prismDRDict['on3TierPeakMonAvgkWh']
#    print prismDRDict['onPeakWOCPPMonAvgkWh']
#    print prismDRDict['offPeakWOCPPMonAvgkWh']
    # Calculate off-peak.
    original_bill = prismDRDict['rateFlat'] * prismDRDict['totalMonAvgkWh']
    if prismDRDict['rateStructure'] == '2tierCPP':
        prismDRDict['rateOffPeak'] = (original_bill - (prismDRDict['rateCPP']*prismDRDict['onPeakWCPPMonAvgkWh'] + prismDRDict['rateOnPeak']*prismDRDict['onPeakWOCPPMonAvgkWh']))/(prismDRDict['offPeakWCPPMonAvgkWh'] + prismDRDict['offPeakWOCPPMonAvgkWh'])
    elif prismDRDict['rateStructure'] == 'PTR':
        prismDRDict['rateOffPeak'] = prismDRDict['rateFlat']
    elif prismDRDict['rateStructure'] == '3tier':
        prismDRDict['rateOffPeak'] = (original_bill - (prismDRDict['rate3Tier']*prismDRDict['on3TierPeakMonAvgkWh'] + prismDRDict['rateOnPeak']*prismDRDict['onPeakWOCPPMonAvgkWh']))/(prismDRDict['offPeakWOCPPMonAvgkWh'])
    else:
        prismDRDict['rateOffPeak'] = (original_bill - (prismDRDict['rateOnPeak']*prismDRDict['onPeakWOCPPMonAvgkWh']))/(prismDRDict['offPeakWOCPPMonAvgkWh'])
    if prismDRDict['rateOffPeak'] < 0:
        print 'ERROR: Off-peak rate is negative :', prismDRDict['rateOffPeak']
#    print prismDRDict['rate3Tier']
#    print prismDRDict['rateOnPeak']
#    print prismDRDict['rateOffPeak']
    #Calculate impact factors for Non-CPP days.
    kWhPerHrOldOnPeakWOCPP = prismDRDict['onPeakWOCPPMonAvgkWh']/prismDRDict['hrsOnPeakPerMonthWOCPP'] # B30
    kWhPerHrOldOffPeakWOCPP = prismDRDict['offPeakWOCPPMonAvgkWh']/prismDRDict['hrsOffPeakPerMonthWOCPP'] #C30
    logFactorWOCPP = math.log(kWhPerHrOldOnPeakWOCPP/kWhPerHrOldOffPeakWOCPP) + prismDRDict['elasticitySubWOCPP'] * (math.log(prismDRDict['rateOnPeak']/prismDRDict['rateOffPeak'] - math.log(prismDRDict['rateFlat']/prismDRDict['rateFlat']))) #B28
    kWhPerHrOldDailyWOCPP = ((kWhPerHrOldOnPeakWOCPP * prismDRDict['numHoursOn']) + (kWhPerHrOldOffPeakWOCPP * prismDRDict['numHoursOff']))/24 #D30
    dailyNewPeakWOCPP = ((prismDRDict['rateOnPeak'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP) + (prismDRDict['rateOffPeak'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D24
    dailyOldPeakWOCPP = ((prismDRDict['rateFlat'] * prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP) + (prismDRDict['rateFlat'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHoursOn'] * kWhPerHrOldOnPeakWOCPP)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D23
    kWhPerHrNewDailyWOCPP = math.exp(math.log(kWhPerHrOldDailyWOCPP) - (prismDRDict['elasticityDailyWOCPP'] * (math.log(dailyOldPeakWOCPP) - math.log(dailyNewPeakWOCPP)))) #D31
    kWhPerHrNewOffPeakWOCPP =  ((24/float(prismDRDict['numHoursOff'])) * kWhPerHrNewDailyWOCPP) / (1+((prismDRDict['numHoursOn']/float(prismDRDict['numHoursOff'])) * math.exp(logFactorWOCPP))) #C31
    kWhPerHrNewOnPeakWOCPP  = kWhPerHrNewOffPeakWOCPP * math.exp(logFactorWOCPP) #B31
    kWhDeltaOnPeakWOCPP = kWhPerHrNewOnPeakWOCPP - kWhPerHrOldOnPeakWOCPP #B32
    kWhDeltaOffPeakWOCPP = kWhPerHrNewOffPeakWOCPP - kWhPerHrOldOffPeakWOCPP #C32
    prismDRDict['impactFactorOnPeakWOCPP'] = kWhDeltaOnPeakWOCPP/kWhPerHrOldOnPeakWOCPP #B33
    prismDRDict['impactFactorOffPeakWOCPP'] = kWhDeltaOffPeakWOCPP/kWhPerHrOldOffPeakWOCPP #C33
    if prismDRDict['rateStructure'] == '3tier':
        kWhPerHrOld3TierPeak = prismDRDict['on3TierPeakMonAvgkWh']/prismDRDict['hrsOn3TierPeak'] # B30
        #kWhPerHrOldOffPeakWOCPP = prismDRDict['offPeakWOCPPMonAvgkWh']/prismDRDict['hrsOffPeakPerMonthWOCPP'] #C30
        logFactor3Tier = math.log(kWhPerHrOld3TierPeak/kWhPerHrOldOffPeakWOCPP) + prismDRDict['elasticitySubWOCPP'] * (math.log(prismDRDict['rate3Tier']/prismDRDict['rateOffPeak'] - math.log(prismDRDict['rateFlat']/prismDRDict['rateFlat']))) #B28
        kWhPerHr3TierOldDaily = ((kWhPerHrOld3TierPeak * prismDRDict['numHours3Tier']) + (kWhPerHrOldOffPeakWOCPP * prismDRDict['numHoursOff']))/24 #D30
        #dailyNew3TierPeak = ((prismDRDict['rate3Tier'] * prismDRDict['numHours3Tier'] * kWhPerHrOld3TierPeak) + (prismDRDict['rateOffPeak'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHours3Tier'] * kWhPerHrOld3TierPeak)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D24
        dailyOld3TierPeak = ((prismDRDict['rateFlat'] * prismDRDict['numHours3Tier'] * kWhPerHrOld3TierPeak) + (prismDRDict['rateFlat'] * prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) / ((prismDRDict['numHours3Tier'] * kWhPerHrOld3TierPeak)+(prismDRDict['numHoursOff'] * kWhPerHrOldOffPeakWOCPP)) #D23
        #kWhPerHrNew3TierDaily = math.exp(math.log(kWhPerHrOld3TierDaily) - (prismDRDict['elasticityDailyWOCPP'] * (math.log(dailyOld3TierPeak) - math.log(dailyNew3TierPeak)))) #D31
        #kWhPerHrNewOffPeakWOCPP =  ((24/float(prismDRDict['numHoursOff'])) * kWhPerHrNew3TierDaily) / (1+((prismDRDict['numHours3Tier']/float(prismDRDict['numHoursOff'])) * math.exp(logFactor3Tier))) #C31
        kWhPerHrNew3TierPeak  = kWhPerHrNewOffPeakWOCPP * math.exp(logFactor3Tier) #B31
        kWhDelta3TierPeak = kWhPerHrNew3TierPeak - kWhPerHrOld3TierPeak #B32
        #kWhDeltaOffPeakWOCPP = kWhPerHrNewOffPeakWOCPP - kWhPerHrOldOffPeakWOCPP #C32
        prismDRDict['impactFactor3TierPeak'] = kWhDelta3TierPeak/kWhPerHrOld3TierPeak #B33
        #prismDRDict['impactFactorOffPeakWOCPP'] = kWhDeltaOffPeakWOCPP/kWhPerHrOldOffPeakWOCPP #C33
    # Calculate CPP days.
    if prismDRDict['rateStructure'] == '2tierCPP' or prismDRDict['rateStructure'] == 'PTR':
        if prismDRDict['rateStructure'] == 'PTR':
            prismDRDict['rateCPP'] = prismDRDict['ratePTR'] + prismDRDict['rateFlat'] #Total value for consumer during PTR periods
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
    print prismDRDict['impactFactor3TierPeak']
    print prismDRDict['impactFactorOnPeakWOCPP']
    print prismDRDict['impactFactorOffPeakWOCPP']
    # Make the modified load curve.
    prismDRDict['modLoad'] = list(prismDRDict['origLoad'])
    for idx, load in enumerate(prismDRDict['origLoad']):
        if idx > prismDRDict['startIndex'] and idx < prismDRDict['stopIndex']: #is hour of year in the cooling season?
            hourOfDay  = idx % 24
            if prismDRDict['rateStructure'] == '2tierCPP':
                if idx in prismDRDict['cppDayIdx']:
                    if (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWCPP'])
                    else:
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWCPP'])
                else:
                    if (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWOCPP'])
                    else:
                        prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWOCPP'])
            if prismDRDict['rateStructure'] == '3tier':
                if (hourOfDay >=  prismDRDict['start3TierHour']) and (hourOfDay <= prismDRDict['stop3TierHour']):
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactor3TierPeak'])
                elif (hourOfDay >= prismDRDict['startHour']) and (hourOfDay <= prismDRDict['stopHour']):
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWOCPP'])
                else:
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWOCPP'])
            else:
                if (hourOfDay < prismDRDict['startHour']) or (hourOfDay > prismDRDict['stopHour']):
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOffPeakWOCPP'])
                else:
                    prismDRDict['modLoad'][idx] = prismDRDict['origLoad'][idx] * (1 + prismDRDict['impactFactorOnPeakWOCPP'])
        #else: #Load outside of cooling season not modified
    return prismDRDict

def _tests():
	# Run PRISM.
	outputs = prism({
        'rateStructure': '3tier', # options: 2tier, 2tierCPP, PTR, 3tier
        'elasticitySubWOCPP': -0.09522, # Substitution elasticty during non-CPP days.
        'elasticityDailyWOCPP': -0.02302, # Daily elasticity during non-CPP days.
        'elasticitySubWCPP': -0.09698, # Substitution elasticty during CPP days. Only required for 2tierCPP
        'elasticityDailyWCPP': -0.01607, # Daily elasticity during non-CPP days. Only reuquired for 2tierCPP
        'startMonth': 5, # 1-12. Beginning month of the cooling season when the DR program will run.
        'stopMonth': 9, # 1-12. Ending month of the cooling season when the DR program will run.
        'startHour': 14, # 0-23. Beginning hour for on-peak and CPP rates.
        'stopHour': 20, # 0-23. Ending hour for on-peak and CPP rates.
        'start3TierHour' : 16, # 0-23 Only required for 3tier. Must be greater than 'startHour' and less than 'stop3TierHour'
        'stop3TierHour' : 16, # 0-23, Only required for 3tier. Must be greater than 'start3TierHour' and less than 'stopHour'
        'rateFlat': 0.15, # pre-DR Time-independent rate paid by residential consumers.
        'rateOnPeak': 0.30, # Peak hour rate on non-CPP days.
        'rate3Tier': 0.90, # Only required for 3tier. Super on-peak rate.
        'rateCPP': 2.80, # Peak hour rate on CPP days. Only required for 2tierCPP
        'ratePTR': 2.65, # Only required for PTR. $/kWh payment to customers for demand reduction on PTR days. Value is entered as a positive value, just like the other rate values, even though it is a rebate.
        'numCPPDays': 10, # Number of CPP days in a cooling season. Only required for 2tierCPP
        'origLoad': [float(x) for x in open('./test_load.csv').readlines()] }) # 8760 load values
	# Write CSV.
	with open('./test_load_modified.csv', 'wb') as outfile:
		for x in outputs['modLoad']:
			outfile.write(str(x) + '\n')
		
if __name__ == '__main__': #Only run if we are calling from the command line, commonly to test functionality
	_tests()