import json, urllib, xml.etree.ElementTree as ET, omf, random, os

def houseSpecs(lat, lon, addressOverride=None):
	''' Get square footage, year built and a few more stats for a house at lat, lon or addressOverride. '''
	# Geo lookup via https://developers.google.com/maps/documentation/geocoding/#ReverseGeocoding
	googleAPI_KEY = ''  # Optional.
	url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng=' + \
		str(lat) + ',' + str(lon) + '&key=' + googleAPI_KEY
	fnameGoog, headers = urllib.urlretrieve(url)
	with open(fnameGoog, 'r') as jsonInput:
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
	fnameZill, headers = urllib.urlretrieve(url)
	# XML parsing.
	xRoot = ET.parse(fnameZill).getroot()
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
	houseArchetypes = omf.feeder.parse('./scratch/uploads/houseArchetypes.glm')
	if pureRandom:
		newHouse = dict(random.choice(houseArchetypes.values()))
		newHouse['name'] = 'REPLACE_ME'
		newHouse['parent'] = 'REPLACE_ME'
		newHouse['schedule_skew'] = str(random.gauss(2000,600))
		# NOTE: average size of US house used below is from http://money.cnn.com/2014/06/04/real_estate/american-home-size/
		newHouse['floor_area'] = str(random.gauss(2600,500))
	else:
		newHouse = {}
		newSpecs = houseSpecs(lat, lon, addressOverride=addressOverride)
		newAge = newSpecs.get('yearBuilt','1980')
		try: intNewAge = int(newAge)
		except: intNewAge = 1980
		def houseMaker(name):
			''' New dict by name from the houseArchetypes. '''
			return dict(houseArchetypes[getByKeyVal(houseArchetypes, 'name', name)])
		if newSpecs['lotSize'] == '': # Make an apartment.
			if intNewAge < 1960: newHouse = houseMaker('R1_Apartment_Pre-1960')
			elif 1960 <= intNewAge < 1990: newHouse = houseMaker('R1_Apartment_1960-1989')
			elif intNewAge >= 1990: newHouse = houseMaker('R1_Apartment_1990-2005')
		else: # Make a house.
			if intNewAge < 1940: newHouse = houseMaker('R1_SingleFamilyHome_Pre-1940')
			elif 1940 <= intNewAge < 1950: newHouse = houseMaker('R1_SingleFamilyHome_1940-1949')
			elif 1950 <= intNewAge < 1960: newHouse = houseMaker('R1_SingleFamilyHome_1950-1959')
			elif 1960 <= intNewAge < 1970: newHouse = houseMaker('R1_SingleFamilyHome_1960-1969')
			elif 1970 <= intNewAge < 1980: newHouse = houseMaker('R1_SingleFamilyHome_1970-1979')
			elif 1980 <= intNewAge < 1990: newHouse = houseMaker('R1_SingleFamilyHome_1980-1989')
			elif intNewAge >= 1990: newHouse = houseMaker('R1_SingleFamilyHome_1990-2005')
		newHouse['name'] = addressOverride
		newHouse['parent'] = 'REPLACE_ME'
		newHouse['schedule_skew'] = str(random.gauss(2000,500))
		newHouse['floor_area'] = newSpecs.get('sqft', '2700')
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

def addScaledRandomHouses(inFeed):
	''' Take a feeder, translate each triplex_node under a meter in to a scaled, semi-randomized house object. '''
	housePath = os.path.join(omf.omfDir, 'scratch', 'uploads', 'houseArchetypes.glm')
	houseArchetypes = omf.feeder.parse(housePath)
	childrenPath = os.path.join(omf.omfDir, 'scratch', 'uploads', 'houseChildren.glm')
	childrenArchetypes = omf.feeder.parse(childrenPath)
	tripNodeKeys = getByKeyVal(inFeed, 'object', 'triplex_node', getAll=True)
	tripLoadKeys = [k for k in tripNodeKeys if 'parent' in inFeed[k]]
	maxKey = omf.feeder.getMaxKey(inFeed) + 1
	inFeed[maxKey] = {'omftype': 'module', 'argument': 'residential'}
	maxKey += 1
	inFeed[maxKey] = {'omftype': '#include','argument': '\"schedulesResponsiveLoads.glm\"'}
	maxKey += 1
	for tripKey in tripLoadKeys:
		tMeter = inFeed[getByKeyVal(inFeed, 'name', inFeed[tripKey]['parent'])]
		tPower = complex(inFeed[tripKey]['power_12']).real
		newHouse = dict(random.choice(houseArchetypes.values()))
		newHouse['name'] += '_' + str(tripKey)
		newHouse['parent'] = tMeter['name']
		newHouse['schedule_skew'] = str(random.gauss(2000,500))
		newHouse['floor_area'] = str(0.50*tPower)
		newHouse['latitude'] = tMeter.get('latitude','0.0')
		newHouse['longitude'] = tMeter.get('longitude','0.0')
		inFeed[maxKey] = newHouse
		maxKey += 1
		for childKey in childrenArchetypes:
			newChild = dict(childrenArchetypes[childKey])
			newChild['name'] += '_' + str(tripKey) + '_' + str(childKey)
			newChild['parent'] = newHouse['name']
			newChild['latitude'] = tMeter.get('latitude','0.0')
			newChild['longitude'] = tMeter.get('longitude','0.0')
			newChild['schedule_skew'] = str(random.gauss(8000,1000))
			inFeed[maxKey] = newChild
			maxKey += 1
		del inFeed[tripKey]

def _tests():
	testFeedPath = os.path.join(omf.omfDir, 'scratch', 'uploads', 'inTest_R4-25.00-1_CLEAN.glm')
	testFeed = omf.feeder.parse(testFeedPath)
	addScaledRandomHouses(testFeed)
	outFilePath = os.path.join(omf.omfDir, 'scratch', 'uploads', 'inTest_R4_modified.glm')
	with open(outFilePath,'w+') as outFile:
		outFile.write(omf.feeder.sortedWrite(testFeed))
	print 'Brooklyn test:', houseSpecs(40.71418, -73.96125), '\n'
	print 'Arlington test:', houseSpecs(38.88358, -77.10193), '\n'
	print 'Override apartment test:', houseSpecs(0,0,addressOverride='3444 N Fairfax Dr, Arlington, VA 22201, USA'), '\n'
	print 'Override house test:', houseSpecs(0,0,addressOverride='1629 North Stafford Street, Arlington, VA 22207, USA'), '\n'
	print 'Full gldHouse test:', gldHouse(0,0,addressOverride='1629 North Stafford Street, Arlington, VA 22207, USA'), '\n'
	# print 'Apt test:', gldHouse(0,0,addressOverride='3444 N Fairfax Dr, Arlington, VA 22201, USA')
	os.remove(outFilePath)

if __name__ == '__main__':
	_tests()