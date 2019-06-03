import json, random
from os.path import join as pJoin

substationlon = -102.765978208
substationlat =   32.993325332

count = 0

substations = 1 
reclosers = 5
meters = 10

#Use kbps for now - add more units for display later
#Using Lora for now
#Using 100 mbps for fiber
#Using 50 kbps for rf 
bitRate = {
	'fiber': 100000000,
	'rf': 50000	
}

#Amount of data to be transferred (will need to adjust based on sampling rate)
#Sampling rate = 5 mins
#Transfer rate 15 minutes
dataSizes = {
	'meter': 4000,
	'gateway': 0,
	'substation': 0,
	'recloser': 0
}

#1-5 per foot
edgeCosts = {
	'fiber': 3,
	'rf':0
}

#transmitter/tower are associated with the gateway - right now adding tower to all gateways
#meter is for each reciever, added reciever to each meter

pointCosts = {
	'meter': 1000,
	'gateway': 30000,
	'substation': 0,
	'recloser': 0
}

#fiber, rf

geoJsonDict = {
"type": "FeatureCollection",
"features": []
}

def newPoint(geodict, pointType, longitude, latitude):
	geodict['features'].append({
		"type": "Feature", 
		"geometry":{
			"type": "Point",
			"coordinates": [longitude, latitude]
		},
		"properties":{
			"name": pointType + str(count),
			"pointType": pointType,
			"cost": pointCosts[pointType]
		}
	})

def newLine(geodict, edgeType, longitude1, latitude1, longitude2, latitude2):
	geodict['features'].append({
		"type": "Feature", 
		"geometry":{
			"type": "LineString",
			"coordinates": [[longitude1, latitude1],[longitude2, latitude2]]
		},
		"properties":{
			"edgeType": edgeType,
			"cost": edgeCosts[edgeType],
			"bandwidth": bitRate[edgeType]
		}
	})

for i in range(substations):
	newPoint(geoJsonDict, 'substation', substationlon, substationlat)
	for i in range(reclosers):
		count+=1
		sign = random.choice([-1, 1])
		recloserlon = substationlon + .001 * random.randint(50, 400) * sign
		sign = random.choice([-1, 1])
		recloserlat = substationlat + .001 * random.randint(50, 400) * sign
		newPoint(geoJsonDict, 'recloser', recloserlon, recloserlat)
		newLine(geoJsonDict, 'fiber', substationlon, substationlat, recloserlon, recloserlat)
		gatewaylon = recloserlon + .0001
		gatewaylat = recloserlat + .0001
		newPoint(geoJsonDict, 'gateway', gatewaylon, gatewaylat)
		newLine(geoJsonDict, 'fiber', recloserlon, recloserlat, gatewaylon, gatewaylat)
		for i in range(meters):
			count+=1
			sign = random.choice([-1, 1])
			meterlon = gatewaylon + .001 * random.randint(10, 40) * sign
			sign = random.choice([-1, 1])
			meterlat = gatewaylat + .001 * random.randint(10, 40) * sign
			newPoint(geoJsonDict, 'meter', meterlon, meterlat)
			newLine(geoJsonDict, 'rf', gatewaylon, gatewaylat, meterlon, meterlat)
print(geoJsonDict)
def getPath(geodict):
	for feature in geodict['features']:
		if feature['geometry']['type'] == 'point':
			print(feature)
			#keep going until hitting transmitter

#getPath(geoJsonDict)
with open('comms.js',"w") as outFile:
	outFile.write("var geojson =")
	json.dump(geoJsonDict, outFile, indent=4)