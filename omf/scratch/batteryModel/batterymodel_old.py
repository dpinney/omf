# -*- coding: utf-8 -*-
"""
Created on Wed May 27 16:59:15 2015

@author: george
"""
def loadDemandCurve(csvFileName="OlinBeckenhamScada.csv"):

    import csv
    import datetime
    import time
    from dateutil.parser import parse

    #  Load our CSV file into a list

    csvFileName="OlinBeckenhamScada.csv"

    demandCurve = []
    for row in csv.DictReader(open(csvFileName)):
        d = parse(row['timestamp'])
        demandCurve.append({'timestamp': int(time.mktime(d.timetuple())), 'month': int(d.month-1), 'day': d.weekday(), 'power': int(row['power'])})
    return demandCurve

def findMonthlyPeaks(dc):
    #  Find peak demand, energy usage and number of readings for every month.

    monthlyPeakDemand  = [0 for x in range(12)]
    for row in dc:
        monthlyPeakDemand[row['month']] = max(row['power'], monthlyPeakDemand[row['month']])
    return monthlyPeakDemand

def batterySim(dc,
               peakShave,           # kW[]
               cellCapacity,        # kWhr
               cellDischarge,       # kW
               cellCharge,          # kW
               cellQty,
               battEff):            # 0<battEff<1
    
    battCapacity    = cellQty * cellCapacity
    battDischarge   = cellQty * cellDischarge
    battCharge      = cellQty * cellCharge
 
    battSoC     = battCapacity                      # Battery state of charge; begins full.
    battDoD     = [battCapacity for x in range(12)] # Depth-of-discharge every month.

    monthlyPeakDemand   = findMonthlyPeaks(dc)

    for row in dc:
        powerUnderPeak  = monthlyPeakDemand[row['month']] - row['power'] - peakShave[row['month']]
        isCharging      = powerUnderPeak > 0
        isDischarging   = powerUnderPeak <= 0


        charge    = isCharging    * min(powerUnderPeak * battEff,   # Charge rate <= new monthly peak - row['power']
                                       battCharge,                  # Charge rate <= battery maximum charging rate.
                                       battCapacity - battSoC)      # Charge rage <= capacity remaining in battery.
        discharge = isDischarging * min(abs(powerUnderPeak),        # Discharge rate <= new monthly peak - row['power']
                                       abs(battDischarge),          # Discharge rate <= battery maximum charging rate.
                                       abs(battSoC+.001))           # Discharge rate <= capacity remaining in battery.
        # (Dis)charge battery
        battSoC += charge
        battSoC -= discharge
        
        row['netpower'] = row['power'] + charge/battEff - discharge


        # Update minimum state-of-charge for this month.
        battDoD[row['month']] = min(battSoC,battDoD[row['month']])
        row['battSoC'] = battSoC
    
    return dc

def findBattDoD(dc,
               peakShave,           # kW[]
               cellCapacity,        # kWhr
               cellDischarge,       # kW
               cellCharge,          # kW
               cellQty,
               battEff):            # 0<battEff<1
    battCapacity    = cellQty * cellCapacity
    battDischarge   = cellQty * cellDischarge
    battCharge      = cellQty * cellCharge
 
    battSoC     = battCapacity                      # Battery state of charge; begins full.
    battDoD     = [battCapacity for x in range(12)] # Depth-of-discharge every month.

    monthlyPeakDemand   = findMonthlyPeaks(dc)

    for row in dc:
        powerUnderPeak  = monthlyPeakDemand[row['month']] - row['power'] - peakShave[row['month']]
        isCharging      = powerUnderPeak > 0
        isDischarging   = powerUnderPeak <= 0


        charge    = isCharging    * min(powerUnderPeak * battEff,   # Charge rate <= new monthly peak - row['power']
                                       battCharge,                  # Charge rate <= battery maximum charging rate.
                                       battCapacity - battSoC)      # Charge rage <= capacity remaining in battery.
        discharge = isDischarging * min(abs(powerUnderPeak),        # Discharge rate <= new monthly peak - row['power']
                                       abs(battDischarge),          # Discharge rate <= battery maximum charging rate.
                                       abs(battSoC+.001))           # Discharge rate <= capacity remaining in battery.
        # (Dis)charge battery
        battSoC += charge
        battSoC -= discharge

        # Update minimum state-of-charge for this month.
        battDoD[row['month']] = min(battSoC,battDoD[row['month']])
    
    return battDoD

def findPeakShave(
            csvFileName="OlinBeckenhamScada.csv",
            cellCapacity  = 100,         # kWhr
            cellDischarge = 30,          # kW
            cellCharge    = 30,          # kW
            cellQty       = 30,
            battEff       = .92):        # 0<battEff<1
    
    dc = loadDemandCurve(csvFileName)
    ps = [cellDischarge * cellQty for x in range(12)]
    
    capacityLimited = True
    while capacityLimited == True:
        battDoD = findBattDoD(dc, ps, cellCapacity, cellDischarge, cellCharge, cellQty, battEff)
        ps = [ps[month]-(battDoD[month] < 0) for month in range(12)]
        capacityLimited = min(battDoD) < 0
    
    oldDemandCurve = [0 for x in range(8784)]
    newDemandCurve = [0 for x in range(8784)]
    
    blah = batterySim(dc, ps, cellCapacity, cellDischarge, cellCharge, cellQty, battEff)
    for idx, row in enumerate(blah):
        oldDemandCurve[idx] = row['power']
        newDemandCurve[idx] = row['netpower']
    return oldDemandCurve, newDemandCurve



import matplotlib.pyplot as plt
(x1, x2) = findPeakShave()
plt.plot(x1)
plt.plot(x2)
plt.show()

# Load demand data
# V&V
# Find monthly peaks
# Find best-case peak-shave
# Record 