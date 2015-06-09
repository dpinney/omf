# -*- coding: utf-8 -*-
"""
Created on Wed May 27 16:59:15 2015

@author: george
"""

import csv
import datetime
import time
from dateutil.parser import parse

def findMonthlyPeaks(csvFileName="OlinBeckenhamScada.csv"):
    #  Find peak demand, energy usage and number of readings for every month.
    csvFileName="OlinBeckenhamScada.csv"
    demandCurve = [{'datetime': parse(row['timestamp']), 'power': int(row['power'])} for row in csv.DictReader(open(csvFileName))]    
    monthlyPeakDemand  = [0 for month in range(12)]

    monthlyPeakDemand = [max(row['power'], monthlyPeakDemand[int(row['datetime'].month)-1]) for idx, row in enumerate(demandCurve)]
    return monthlyPeakDemand

def batterySim(csvFileName,
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
    csvFileName="OlinBeckenhamScada.csv"
    dc = [{'datetime': parse(row['timestamp']), 'power': int(row['power'])} for row in csv.DictReader(open(csvFileName))]     

    monthlyPeakDemand   = findMonthlyPeaks(dc)

    for row in dc:
        month = int(row['datetime'].month)-1
        powerUnderPeak  = monthlyPeakDemand[month] - row['power'] - peakShave[month]
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
        battDoD[month] = min(battSoC,battDoD[month])
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
        month = int(row['datetime'].month)-1
        powerUnderPeak  = monthlyPeakDemand[month] - row['power'] - peakShave[month]
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
        battDoD[month] = min(battSoC,battDoD[month])
    
    return battDoD

def findPeakShave(
            csvFileName="/home/george/OlinBeckenhamScada.csv",
            cellCapacity  = 100,         # kWhr
            cellDischarge = 30,          # kW
            cellCharge    = 30,          # kW
            cellQty       = 1,
            battEff       = .92):        # 0<battEff<1
    import itertools
    dc = [{'datetime': parse(row['timestamp']), 'power': int(row['power'])} for row in csv.DictReader(open(csvFileName))]     
    ps = [cellDischarge * cellQty for x in range(12)]
    
    capacityLimited = True
    while capacityLimited == True:
        battDoD = findBattDoD(dc, ps, cellCapacity, cellDischarge, cellCharge, cellQty, battEff)
        ps = [ps[month]-(battDoD[month] < 0) for month in range(12)]
        capacityLimited = min(battDoD) < 0

  #  dcGroupByMonth = [groupby(dc['month'])[x] for x in range(12)]
    dcThroughTheMonth = [[t for t in iter(dc) if t['datetime'].month-1<=x] for x in range(12)]
    hoursThroughTheMonth = [len(dcThroughTheMonth[month]) for month in range(12)]


    
    oldDemandCurve = [0 for x in range(8784)]
    newDemandCurve = [0 for x in range(8784)]
    
    batterySimulation = batterySim(dc, ps, cellCapacity, cellDischarge, cellCharge, cellQty, battEff)
    
    oldDemandCurve = [t['power'] for t in batterySimulation]
    newDemandCurve = [t['netpower'] for t in batterySimulation]
    return oldDemandCurve, newDemandCurve, hoursThroughTheMonth





import matplotlib.pyplot as plt
(x1, x2, x3) = findPeakShave()
plt.plot(x1)
plt.plot(x2)
for month in range(12):
  plt.axvline(x3[month])
plt.show()
print x3

# Load demand data
# V&V
# Return demand curve

# Find monthly peaks
# Find best-case peak-shave
# Record best-case dispatch: demand before/after, battSoC
# Plot demand before and after with vertical lines between months.
# Show battDoD for 8760 below demand before and after chart.
# Financial variables --SPP. NPV, cash-flow curve
# Nice to have: LCOE