import json, urllib, xml.etree.ElementTree as ET, omf, random

def house(lat, lon, addressOverride=None):
	''' Get square footage, year built and a few more stats for a house at lat, lon or addressOverride. '''
	# Geo lookup via https://developers.google.com/maps/documentation/geocoding/#ReverseGeocoding
	googleAPI_KEY = ''  # Optional.
	url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + \
		str(lat) + ',' + str(lon) + '&key=' + googleAPI_KEY
	filename = 'out_addressAtLatlon_' + str(lat) + '_' + str(lon) + '.json'
	urllib.urlretrieve(url, filename)
	with open(filename, 'r') as jsonInput:
		response_data = json.load(jsonInput)
	try:
		firstAdd = response_data['results'][0]['formatted_address']
	except:
		if addressOverride: firstAdd = addressOverride
		else: return None
	addr_ptrn = firstAdd.split(', ')
	street_number = addr_ptrn[0]
	city_name = addr_ptrn[1]
	state_name = addr_ptrn[2].split(' ')[0]
	zip_code = addr_ptrn[2].split(' ')[1]
	country_name = addr_ptrn[3]
	# House details lookup via http://www.zillow.com/howto/api/GetDeepSearchResults.htm
	zwsID = 'X1-ZWz1dvjlzatudn_5m9vn'  # TODO: change to a new one
	url = 'http://www.zillow.com/webservice/GetDeepSearchResults.htm?zws-id=' + \
		zwsID + '&address=' + \
		street_number.replace(' ', '+') + '&citystatezip=' + zip_code
	filename = 'out_houseInfo_' + str(lat) + '_' + str(lon) + '.xml'
	urllib.urlretrieve(url, filename)
	# XML parsing.
	xRoot = ET.parse(filename).getroot()
	try:
		results = xRoot.find('response').find('results').findall('result')
		matches = len(results) # We warn user by putting # of matches in the output.
		if matches <1: return None
		result = results[0]
	except:
		return None
	def safeText(key):
		try: return result.find(key).text
		except: return ''
	house_info = {'lat': lat, 'lon': lon, 'object': 'house', 'address': firstAdd,
		'matches':matches,
		'sqft':safeText('finishedSqFt'),
		'lotSize':safeText('lotSizeSqFt'),
		'bathrooms':safeText('bathrooms'),
		'bedrooms': safeText('bedrooms'),
		'yearBuilt': safeText('yearBuilt')}
	return house_info

def gldHouse(lat, lon, addressOverride=None, pureRandom=False):
	''' Given a lat/lon, address, return a GLD house object modeling that location.
	Or just return a totally random GLD house. '''
	houseArchetypes = omf.feeder.parse('houseArchetypes.glm')
	if pureRandom:
		newHouse = dict(random.choice(houseArchetypes.values()))
		newHouse['name'] = 'REPLACE_ME'
		newHouse['parent'] = 'REPLACE_ME'
		newHouse['schedule_skew'] = str(random.gauss(2000,100))
		newHouse['floor_area'] = str(random.gauss(6000,1000))
	elif addressOverride:
		houseStats = house(0, 0, addressOverride=addressOverride)
		newHouse = {'name':addressOverride, 'parent':'REPLACE_ME'}
		#TODO: finish implementation.
	else:
		houseStats = house(lat, lon)
		newHouse = {}
		#TODO: finish implementation.	
	return newHouse

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

def _gldTests():
	testFeed = omf.feeder.parse('inTest_R4-25.00-1_CLEAN.glm')
	addScaledHouses(testFeed)
	with open('inTest_R4_modified.glm','w+') as outFile:
		outFile.write(omf.feeder.sortedWrite(testFeed))

if __name__ == '__main__':
	print 'Brooklyn test:', house(40.71418, -73.96125)
	print 'Arlington test:', house(38.88358, -77.10193)
	print 'Override test:', house(0,0,addressOverride='3444 N Fairfax Dr, Arlington, VA 22201, USA')
