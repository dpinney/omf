# -*- coding: utf-8 -*-
"""
Created on Wed May 27 16:59:15 2015
@author: george
"""

import  csv
import  datetime
import  time
import  itertools
from  dateutil.parser import parse

def findPeakShave(
            csvFileName="OlinBeckenhamScada.csv",
            cellCapacity  = 100,         # kWhr
            cellDischarge = 30,          # kW
            cellCharge    = 30,          # kW
            cellQty       = 3,
            battEff       = .92):        # 0<battEff<1

    battCapacity    = cellQty * cellCapacity
    battDischarge   = cellQty * cellDischarge
    battCharge      = cellQty * cellCharge

    dc = [{'datetime': parse(row['timestamp']), 'power': int(row['power'])} for row in csv.DictReader(open(csvFileName))]
    
    for row in dc:
        row['month'] = row['datetime'].month-1
        row['weekday'] = row['datetime'].weekday

    ps = [battDischarge for x in range(12)]
    dcGroupByMonth = [[t['power'] for t in dc if t['datetime'].month-1==x] for x in range(12)]
    monthlyPeakDemand = [max(dcGroupByMonth[x]) for x in range(12)]
    print monthlyPeakDemand
    
    capacityLimited = True
    while capacityLimited == True:
        battSoC     = battCapacity                      # Battery state of charge; begins full.
        battDoD     = [battCapacity for x in range(12)] # Depth-of-discharge every month.
        for row in dc:
            month = int(row['datetime'].month)-1
            powerUnderPeak  = monthlyPeakDemand[month] - row['power'] - ps[month]

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
            row['netpower'] = row['power'] + charge/battEff - discharge
            row['battSoC'] = battSoC

        capacityLimited = min(battDoD) < 0
        ps = [ps[month]-(battDoD[month] < 0) for month in range(12)]


  #  dcGroupByMonth = [groupby(dc['month'])[x] for x in range(12)]
    dcThroughTheMonth = [[t for t in iter(dc) if t['datetime'].month-1<=x] for x in range(12)]
    hoursThroughTheMonth = [len(dcThroughTheMonth[month]) for month in range(12)]
    
    oldDemandCurve = [t['power'] for t in dc]
    newDemandCurve = [t['netpower'] for t in dc]
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