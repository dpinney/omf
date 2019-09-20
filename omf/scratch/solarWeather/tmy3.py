import requests
import os
from math import cos, asin, sqrt
import csv

URL = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3' 

example_file = '722287TYA.CSV'

def tmy3_pull(usafn_number, out_file=None):
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3'
	file_name = '{}.CSV'.format(usafn_number)
	file_path = os.path.join(url, file_name)
	data = requests.get(file_path)
	if out_file is not None:
		csv_lines = data.iter_lines()
		reader = csv.reader(csv_lines, delimiter=',')
		if out_file is not None:
			with open(out_file, 'w') as csvfile:
				#can use following to skip first line to line up headers
				#reader.next()
				for i in reader:
					csvwriter = csv.writer(csvfile, delimiter=',')
					csvwriter.writerow(i)
	else:
		return resp

#1020 usafn codes
#use latitude/longitude for lookup
def tmy3_station_meta():
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3'
	file_name = 'TMY3_StationsMeta.csv'
	file_path = os.path.join(url, file_name)
	resp = requests.get(file_path)
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

if __name__== '__main__':
	tmy3_pull('722287TYA', 'tmy.csv')
	tmy3_station_meta()