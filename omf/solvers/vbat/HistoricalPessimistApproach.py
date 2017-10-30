import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from operator import sub
import collections
#The demand:
#demand = [1000,1000,1000,1000,1000,1025,1050,1075,1125,1200,1450,1750,1900,2000,1900,1750,1450,1200,1125,1075,1050,1025,1000,1000]

demand = collections.OrderedDict()
demand[0.25] = 1000
demand[0.5] = 1000
demand[0.75] = 1000
demand[1] = 1000
demand[1.25] = 1000
demand[1.5] = 1000
demand[1.75] = 1000
demand[2] = 1000
demand[2.25] = 1000
demand[2.5] = 1000
demand[2.75] = 1000
demand[3] = 1000
demand[3.25] = 1000
demand[3.5] = 1000
demand[3.75] = 1000
demand[4] = 1000
demand[4.25] = 1000
demand[4.5] = 1002
demand[4.75] = 1005
demand[5] = 1009
demand[5.25] = 1014
demand[5.5] = 1020
demand[5.75] = 1027
demand[6] = 1035
demand[6.25] = 1045
demand[6.5] = 1057
demand[6.75] = 1070
demand[7] = 1085
demand[7.25] = 1100
demand[7.5] = 1120
demand[7.75] = 1145
demand[8] = 1175
demand[8.25] = 1210
demand[8.5] = 1255
demand[8.75] = 1310
demand[9] = 1375
demand[9.25] = 1450
demand[9.5] = 1520
demand[9.75] = 1585
demand[10] = 1645
demand[10.25] = 1700
demand[10.5] = 1750
demand[10.75] = 1795
demand[11] = 1835
demand[11.25] = 1871
demand[11.5] = 1903
demand[11.75] = 1930
demand[12] = 1951
demand[12.25] = 1965
demand[12.5] = 1975
demand[12.75] = 1983
demand[13] = 1989
demand[13.25] = 1993
demand[13.5] = 1996
demand[13.75] = 1998
demand[14] = 2000
demand[14.25] = 1998
demand[14.5] = 1996
demand[14.75] = 1993
demand[15] = 1989
demand[15.25] = 1983
demand[15.5] = 1975
demand[15.75] = 1965
demand[16] = 1951
demand[16.25] = 1930
demand[16.5] = 1903
demand[16.75] = 1871
demand[17] = 1835
demand[17.25] = 1795
demand[17.5] = 1750
demand[17.75] = 1700
demand[18] = 1645
demand[18.25] = 1585
demand[18.5] = 1520
demand[18.75] = 1450
demand[19] = 1375
demand[19.25] = 1310
demand[19.5] = 1255
demand[19.75] = 1210
demand[20] = 1175
demand[20.25] = 1145
demand[20.5] = 1120
demand[20.75] = 1100
demand[21] = 1085
demand[21.25] = 1070
demand[21.5] = 1057
demand[21.75] = 1045
demand[22] = 1035
demand[22.25] = 1027
demand[22.5] = 1020
demand[22.75] = 1014
demand[23] = 1009
demand[23.25] = 1005
demand[23.5] = 1002
demand[23.75] = 1000
demand[24] = 1000

plt.plot(*zip(*sorted(demand.items())))
plt.ylabel('Demand in kW')
plt.xlabel('Hour of the day')
plt.axis([0,24,0,2200])


#peak demand
peakDemand = 0
for x in demand:
	if demand[x] > peakDemand:
		peakDemand = demand[x]
		peakDemandHour = x
print str(peakDemand) + ' kW is reached at: ' + str(peakDemandHour)



peakWidth = 4
startingPeakHour = peakDemandHour - peakWidth/2
endingPeakHour = peakDemandHour + peakWidth/2

print ("Since the peak is reached at: " + str(peakDemandHour)
	+ " we estimate the peak usage range from: " + str(startingPeakHour) + " to " + str(endingPeakHour))


powerThreshold = demand[startingPeakHour]
print "The power threshold for the peak usage region is: " + str(powerThreshold) + " kW"


adjustedDemand = collections.OrderedDict()
energyShaved = 0
for x in demand:
	if x>=startingPeakHour and x<=endingPeakHour:
		adjustedDemand[x] = powerThreshold
		energyShaved = float(energyShaved) + (float(demand[x]) - float(powerThreshold))*24/float(len(demand))
	else:
		adjustedDemand[x] = demand[x]

print "The energy shaved is: " + str(energyShaved) + " kWh"
#print demand




plt.plot(*zip(*sorted(adjustedDemand.items())))
		#powerShaved = 
'''
peakCutOff =[0]*24
cutOff = demand[startingPeakHour]

for x in xrange(0,23):
	if demand[x] < cutOff:
		peakCutOff[x] = 0
	else:
		peakCutOff[x] = demand[x]-cutOff

print demand
print peakCutOff

energyShaved = peakWidth*(peakDemand-demand[startingPeakHour])/2 #assuming peak is a triangle we calculate the area to get the energy
print "The energy shaved is: " + str(energyShaved) + " kWh"

adjustedDemand = map(sub,demand,peakCutOff)

#red_patch = mpatches.Patch(color='red', label='The red data')

#plt.legend(red_patch)

plt.grid()
plt.plot(peakCutOff)
plt.plot(adjustedDemand)
'''
plt.show()
