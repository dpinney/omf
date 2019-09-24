import requests
import os
import csv

API_KEY = 'rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56'

class NSRDB():
	def __init__(self, data_set, longitude, latitude, year, api_key, utc='true', leap_day='false', email='erikjamestalbot@gmail.com', interval=None):
		self.base_url = 'https://developer.nrel.gov'
		self.data_set = data_set
		self.params = {}
		self.params['api_key'] = api_key
		#wkt will be one point to use csv option - may need another call to get correct wkt value: https://developer.nrel.gov/docs/solar/nsrdb/nsrdb_data_query/
		self.params['wkt'] = self.latlon_to_wkt(longitude, latitude)
		#names will be one value to use csv option
		self.params['names'] = str(year)
		#note utc must be either 'true' or 'false' as a string, not True or False Boolean value
		self.params['utc'] = utc
		self.params['leap_day'] = leap_day
		self.params['email'] = email
		self.interval = interval

	def latlon_to_wkt(self, longitude, latitude):
		if latitude < -90 or latitude > 90:
			raise('invalid latitude')
		elif longitude < -180 or longitude > 180:
			raise('invalid longitude')  
		return 'POINT({} {})'.format(longitude, latitude)

	def create_url(self, route):
		return os.path.join(self.base_url, route)

	#physical solar model
	def psm(self):
		self.params['interval'] = self.interval
		route = 'api/solar/nsrdb_psm3_download.csv'
		self.request_url = self.create_url(route)

	#physical solar model v3 tsm
	def psm_tmy(self):
		route = 'api/nsrdb_api/solar/nsrdb_psm3_tmy_download.csv'
		self.request_url = self.create_url(route)

	#SUNY international
	def suny(self):
		route = 'api/solar/suny_india_download.csv'
		self.request_url = self.create_url(route)

	#spectral tmy
	def spectral_tmy(self):
		route = 'api/nsrdb_api/solar/spectral_tmy_india_download.csv'
		self.request_url = self.create_url(route)

	#makes api request based on inputs and returns the response object
	def execute_query(self):
		set_query = getattr(self, self.data_set)
		set_query()
		resp = requests.get(self.request_url, params=self.params)
		return resp

'''Create nrsdb factory and execute query. Optional output to file or return the response object.'''
def get_nrsdb_data(data_set, longitude, latitude, year, api_key, utc='true', leap_day='false', email='erikjamestalbot@gmail.com', interval=None, out_file=None):
	nrsdb_factory = NSRDB(data_set, longitude, latitude, year, api_key, utc=utc, leap_day=leap_day, email=email, interval=interval)
	data = nrsdb_factory.execute_query()
	csv_lines = data.iter_lines()
	reader = csv.reader(csv_lines, delimiter=',')
	if out_file is not None:
		with open(out_file, 'w') as csvfile:
			for i in reader:
				csvwriter = csv.writer(csvfile, delimiter=',')
				csvwriter.writerow(i)
	else:
		#Maybe change depending on what's easy/flexible but this gives good display
		return data.text

if __name__ == '__main__':
	get_nrsdb_data('psm',-99.49218,43.83452,'2017', API_KEY, interval=60, out_file='psm.csv')
	print(get_nrsdb_data('psm',-99.49218,43.83452,'2017', API_KEY, interval=60))
	get_nrsdb_data('psm_tmy',-99.49218,43.83452,'tdy-2017', API_KEY, out_file='psm_tmy.csv')
	get_nrsdb_data('suny',77.1679,22.1059,'2014', API_KEY, out_file='suny.csv')
	get_nrsdb_data('spectral_tmy',77.08007,20.79720,'tmy', API_KEY, out_file='spectral_tmy.csv')