import json
import urllib
import xml.etree.ElementTree as ET
import omf
import random

def house(lat, lon):
	house_info = dict()
	# Geo lookup:
	# https://developers.google.com/maps/documentation/geocoding/#ReverseGeocoding
	googleAPI_KEY = ''  # TODO: get a new one
	url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + \
		str(lat) + ',' + str(lon) + '&key=' + googleAPI_KEY
	filename = 'out_house_' + str(lat) + '_' + str(lon) + '.json'
	urllib.urlretrieve(url, filename)
	with open(filename, 'r') as jsonInput:
		response_data = json.load(jsonInput)
	if response_data['status'] != 'OK':
		return None
	for address in response_data['results']:
		if 'street_address' in address['types']:
			addr = address['formatted_address']
			addr_ptrn = addr.split(', ')
			street_number = addr_ptrn[0]
			city_name = addr_ptrn[1]
			state_name = addr_ptrn[2].split(' ')[0]
			zip_code = addr_ptrn[2].split(' ')[1]
			country_name = addr_ptrn[3]
	# zillow lookup: http://www.zillow.com/howto/api/GetDeepSearchResults.htm
	zwsID = 'X1-ZWz1dvjlzatudn_5m9vn'  # TODO: change to a new one
	url = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?zws-id=' + \
		zwsID + '&address=' + \
		street_number.replace(' ', '+') + '&citystatezip=' + zip_code
	filename = 'out_property_' + str(lat) + '_' + str(lon) + '.xml'
	urllib.urlretrieve(url, filename)
	#  TODO: better xml parsing
	xml_tree = ET.parse(filename)
	root = xml_tree.getroot()
	if root[1][1].text != str(0):
		return None
	lotSizeSqFt = root[2][0][0][8].text
	finishedSqFt = root[2][0][0][9].text
	bathrooms = root[2][0][0][10].text
	bedrooms = root[2][0][0][11].text
	house_info = {'object': 'house', 'sqft': lotSizeSqFt, 'bathrooms':
				  bathrooms, 'bedrooms': bedrooms, 'lat': lat, 'lon': lon, 'address': addr}
	print house_info
	return house_info

def getByKeyVal(tree, key, value, getAll=False):
	''' Return (one or more) keys to the first item in tree where that objects key=val.'''
	allMatches = [k for k in tree if tree[k].get(key,'') == value]
	if getAll:
		return allMatches
	elif (not getAll) and len(allMatches) > 0:
		return allMatches[0]
	else:
		return None

def addScaledHouses(inFeed):
	''' Take a feeder, translate each triplex_node under a meter in to a scaled, semi-randomized house object. '''
	houseArchetypes = omf.feeder.parse('houseArchetypes.glm')
	tripNodeKeys = getByKeyVal(inFeed, 'object', 'triplex_node', getAll=True)
	tripLoadKeys = [k for k in tripNodeKeys if 'parent' in inFeed[k]]
	maxKey = omf.feeder.getMaxKey(inFeed) + 1
	inFeed[maxKey] = {"omftype": "module", "argument": "residential"}
	maxKey += 1
	# from pprint import pprint as pp; pp(houseArchetypes)
	for i, tripKey in enumerate(tripLoadKeys):
		tMeter = inFeed[getByKeyVal(inFeed, 'name', inFeed[tripKey]['parent'])]
		tPower = float(inFeed[tripKey]['power_1'].replace('j','').split('+')[0])
		newHouse = dict(random.choice(houseArchetypes.values()))
		newHouse['name'] += '_' + str(i)
		newHouse['parent'] = tMeter['name']
		newHouse['schedule_skew'] = str(random.gauss(2000,100))
		newHouse['floor_area'] = str(0.50*float(tPower))
		inFeed[maxKey + i] = newHouse

def _testHouseGeo():
	lat = 40.71418
	lon = -73.96125
	if house(lat, lon) != None:
		print 'Test passed!'
	else:
		print 'House is not found!'

def _tests():
	testFeed = omf.feeder.parse('inTest_R4-25.00-1_CLEAN.glm')
	addScaledHouses(testFeed)
	with open('inTest_R4_modified.glm','w+') as outFile:
		outFile.write(omf.feeder.sortedWrite(testFeed))

if __name__ == '__main__':
	_testHouseGeo()
