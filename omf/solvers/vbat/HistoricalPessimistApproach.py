import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from operator import sub
#The demand:
demand = [1000,1000,1000,1000,1000,1025,1050,1075,1125,1200,1450,1750,1900,2000,1900,1750,1450,1200,1125,1075,1050,1025,1000,1000]
plt.plot(demand)
plt.ylabel('Demand in kW')
plt.xlabel('Hour of the day')
plt.axis([0,23,0,2200])
#peak demand
peakDemand = max(demand)
#time at which peak demand is reached
peakDemandHour = demand.index(peakDemand)

peakWidth = 3
startingPeakHour = peakDemandHour - peakWidth/2
endingPeakHour = peakDemandHour + peakWidth/2

peakCutOff =[0]*24
cutOff = demand[startingPeakHour]
'''peakCutOff[startingPeakHour:endingPeakHour] = [demand[peakDemandHour] - demand[startingPeakHour]]
print peakCutOff'''
'''for x in peakCutOff[x]:
	print x
	if x>=startingPeakHour and x<=endingPeakHour:
		peakCutOff[x] = demand[x] - demand[startingPeakHour]'''

for x in xrange(0,23):
	if demand[x] < cutOff:
		peakCutOff[x] = 0
	else:
		peakCutOff[x] = demand[x]-cutOff

'''peakCutOff[startingPeakHour] = 0
peakCutOff[peakDemandHour] = demand[peakDemandHour] - demand[startingPeakHour]
peakCutOff[endingPeakHour] = 0'''
print demand
print peakCutOff

energyShaved = peakWidth*(peakDemand-demand[startingPeakHour])/2
print "The energy shaved is: " + str(energyShaved) + " kWh"

adjustedDemand = map(sub,demand,peakCutOff)

#red_patch = mpatches.Patch(color='red', label='The red data')

#plt.legend(red_patch)

plt.grid()
plt.plot(peakCutOff)
plt.plot(adjustedDemand)
plt.show()
