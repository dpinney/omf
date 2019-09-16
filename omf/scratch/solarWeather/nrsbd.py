import requests
import os

API_KEY = 'rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56'

#resp = requests.get('https://developer.nrel.gov/api/nsrdb_api/solar/nsrdb_psm3_tmy_download.csv?api_key=rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56&wkt=POINT(-99.49218%2043.83452)&attributes=dhi%2Cdni%2Cghi%2Cdew_point%2Cair_temperature%2Csurface_pressure%2Cwind_direction%2Cwind_speed%2Csurface_albedo%2C%2C%2C&names=tmy-2016&full_name=Louis%20Bourbon&email=erikjamestalbot@gmail.com&affiliation=NREL&mailing_list=false&reason=test&utc=true')
#print(resp.text)

class NSRDB():
	def __init__(self, data_set, longitude, latitude, year, utc='true', leap_day='false', email='erikjamestalbot@gmail.com', interval=None):
		self.base_url = 'https://developer.nrel.gov'
		self.data_set = data_set
		self.params = {}
		self.params['api_key'] = API_KEY
		#wkt will be one point to use csv option - may need another call to get correct wkt value: https://developer.nrel.gov/docs/solar/nsrdb/nsrdb_data_query/
		self.params['wkt'] = self.latlon_to_wkt(longitude, latitude)
		#attributes will vary / leave out and get all attributes
		#self.attributes = []
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

	#makes api request based on inputs
	def execute_query(self):
		set_query = getattr(self, self.data_set)
		set_query()
		resp = requests.get(self.request_url, params=self.params)
		return resp.text

def get_nrsdb_data(data_set, longitude, latitude, year, utc='true', leap_day='false', email='erikjamestalbot@gmail.com', interval=None):
	nrsdb_factory = NSRDB(data_set, longitude, latitude, year, utc=utc, leap_day=leap_day, email=email, interval=interval)
	return nrsdb_factory.execute_query()

if __name__ == '__main__':
	print(get_nrsdb_data('psm',-99.49218,43.83452,'2017', interval=60))
	print(get_nrsdb_data('psm_tmy',-99.49218,43.83452,'tdy-2017'))
	print(get_nrsdb_data('suny',77.1679,22.1059,'2014'))
	print(get_nrsdb_data('spectral_tmy',77.08007,20.79720,'tmy'))
