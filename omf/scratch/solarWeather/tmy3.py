import requests
import os
from math import cos, asin, sqrt
import csv

URL = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3' 

example_file = '722287TYA.CSV'

'''Pull TMY3 data based on usafn. Use nearest_tmy3_station function to get a close by tmy3 station based on latitude/longitude coordinates '''
def tmy3_pull(usafn_number, out_file=None):
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3'
	file_name = '{}TYA.CSV'.format(usafn_number)
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

'''Return nearest USAFN stattion based on latlon'''
def nearest_tmy3_station(latitude, longitude):
	url = 'https://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3'
	file_name = 'TMY3_StationsMeta.csv'
	file_path = os.path.join(url, file_name)
	data = requests.get(file_path)
	csv_lines = data.iter_lines()
	reader = csv.DictReader(csv_lines, delimiter=',')
	#SHould file be local?
	#with open('TMY3_StationsMeta.csv', 'r') as metafile:
	#reader = csv.DictReader(metafile, delimiter=',')
	tmy3_stations = [station for station in reader]
	nearest = min(tmy3_stations, key=lambda station: lat_lon_diff(latitude, station['Latitude'], longitude, station['Longitude']))
	return nearest['USAF']
		
	'''
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
		return data.text'''
def lat_lon_diff(lat1, lat2, lon1, lon2):
	'''Get the distance between two sets of latlon coordinates'''
	dist = sqrt((float(lat1) - float(lat2))**2 + (float(lon1) - float(lon2))**2)
	return dist

if __name__== '__main__':
	tmy3_pull(nearest_tmy3_station(41, -78), out_file='tmy3_test.csv')