import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from operator import sub
demand = [1000,1000,1000,1000,1000,1025,1050,1075,1125,1200,1450,1750,1900,2000,1900,1750,1450,1200,1125,1075,1050,1025,1000,1000]
plt.plot(demand)
#plt.plot([1000,1000,1000,1000,1000,1025,1050,1075,1125,1200,1450,1750,1900,2000,1900,1750,1450,1200,1125,1075,1050,1025,1000,1000])
#plt.plot([datapoints])
plt.ylabel('Demand in kW')
plt.xlabel('Hour of the day')
plt.axis([0,23,0,2200])
peakDemand = max(demand)
peakDemandHour = demand.index(peakDemand)
peakWidth = 2
startingPeakHour = peakDemandHour - peakWidth/2
endingPeakHour = peakDemandHour + peakWidth/2
#print startingPeakHour
#print endingPeakHour
peakCutOff = [0]*24
peakCutOff[startingPeakHour] = 0
peakCutOff[peakDemandHour] = demand[peakDemandHour] - demand[startingPeakHour]
peakCutOff[endingPeakHour] = 0
#print peakCutOff
energyShaved = peakWidth*(peakDemand-demand[startingPeakHour])/2
print "The energy shaved is: " + str(energyShaved) + " kWh"

adjustedDemand = map(sub,demand,peakCutOff)

#red_patch = mpatches.Patch(color='red', label='The red data')

#plt.legend(red_patch)

plt.grid()
plt.plot(peakCutOff)
plt.plot(adjustedDemand)
plt.show()
