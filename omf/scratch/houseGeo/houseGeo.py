import json
import urllib
import xml.etree.ElementTree as ET


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

def addHouses(feeder):
    ''' '''
    #TODO: implement me.
    return

def _tests():
    lat = 40.71418
    lon = -73.96125
    if house(lat, lon) != None:
        print 'Test passed!'
    else:
        print 'House is not found!'

if __name__ == '__main__':
    _tests()
