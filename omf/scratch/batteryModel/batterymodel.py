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
            cellDischarge = 50,          # kW
            cellCharge    = 50,          # kW
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
    
    oldDemandCurve  = [t['power'] for t in dc]
    newDemandCurve  = [t['netpower'] for t in dc]
    battSoCCurve    = [t['battSoC'] for t in dc]

    
    
    return oldDemandCurve, newDemandCurve, hoursThroughTheMonth, battSoCCurve, ps

import matplotlib.pyplot as plt
(oldCurve, newCurve, hoursThroughTheMonth, battSoCCurve, peakShave) = findPeakShave()

demandCharge    = 10    # USD
discountRate    = .025  # APR
numberOfYears   = 10    # Years
cellCost        = 25000
cellQty         = 3

peakShaveSum = sum(peakShave)

spp = (cellCost*cellQty)/(peakShaveSum*demandCharge)
print "Simple payback period for this battery is %d" % spp

cashFlowCurve = [peakShaveSum * demandCharge for year in range(numberOfYears)]
cashFlowCurve[0]-= (cellCost * cellQty)

npv = 0.0
for idx, annualCashFlow in enumerate(cashFlowCurve):
    npv += annualCashFlow/(1+discountRate)**idx
print "Net Present Value %d for this battery is %d" % (numberOfYears, npv)



plt.plot(oldCurve)
plt.plot(newCurve)
plt.plot(battSoCCurve)
for month in range(12):
  plt.axvline(hoursThroughTheMonth[month])
plt.show()
print hoursThroughTheMonth
print peakShaveSum

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