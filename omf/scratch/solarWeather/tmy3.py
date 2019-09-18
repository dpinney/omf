import requests
import os
from math import cos, asin, sqrt

URL = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3' 

example_file = '722287TYA.CSV'

def tmy3_pull(usafn_number):
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3'
	file_name = '{}.CSV'.format(usafn_number)
	print(file_name)
	file_path = os.path.join(url, file_name)
	print(file_path)
	resp = requests.get(file_path)
	print(resp)
	print(resp.text)
	return resp.text

#1020 usafn codes
#use latitude/longitude for lookup
def tmy3_station_meta():
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3'
	file_name = 'TMY3_StationsMeta.csv'
	file_path = os.path.join(url, file_name)
	resp = requests.get(file_path)
	print(resp.text)
	return resp.text

def usaf_by_coords(latitude, longitude):
	pass

#finding distance - need to validate
def distance(lat1, lon1, lat2, lon2):
	p = math.PI / 180
	a = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
	return 12742 * asin(sqrt(a))

#finding closest - need to validate
def closest(data, v):
	return min(data, key=lambda p: distance(v['lat'],v['lon'],p['lat'],p['lon']))

if __name__= 'main':
	tmy3_pull('722287TYA')
	tmy3_station_meta()