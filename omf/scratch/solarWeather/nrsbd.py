import requests
import os

API_KEY = 'rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56'

#resp = requests.get('https://developer.nrel.gov/api/nsrdb_api/solar/nsrdb_psm3_tmy_download.csv?api_key=rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56&wkt=POINT(-99.49218%2043.83452)&attributes=dhi%2Cdni%2Cghi%2Cdew_point%2Cair_temperature%2Csurface_pressure%2Cwind_direction%2Cwind_speed%2Csurface_albedo%2C%2C%2C&names=tmy-2016&full_name=Louis%20Bourbon&email=erikjamestalbot@gmail.com&affiliation=NREL&mailing_list=false&reason=test&utc=true')
#print(resp.text)

class NSRBD():
	def __init__(self, data_set, longitude, latitude, year, utc=True, leap_day=False, email=None, interval=None):
		self.base_url = 'https://developer.nrel.gov'
		self.data_set = data_set
		self.params = {}
		self.params['api_key'] = API_KEY
		self.params['attributes'] = 'dhi'
		#wkt will be one point
		self.params['wkt'] = self.latlon_to_wkt(longitude, latitude)
		#attributes will vary / leave out and get all attributes
		#self.attributes = []
		#names will be one value
		self.params['names'] = str(year)
		#self.params['utc'] = utc
		#self.params['leap_day'] = leap_day
		self.params['email'] = email
		query = getattr(self,data_set)
		query()

	def latlon_to_wkt(self, longitude, latitude):
		if latitude < -90 or latitude > 90:
			raise('invalid latitude')
		elif longitude < -180 or longitude > 180:
			raise('invalid longitude')  
		return 'POINT({} {})'.format(longitude, latitude)

	def create_url(self, route):
		return os.path.join(self.base_url, route)

	#physical solar model
	def psm(self, interval):
		self.params['interval'] = interval
		route = 'api/solar/nsrdb_psm3_download.csv'
		self.request_url = self.create_url(route)
		pass

	#physical solar model v3 tsm
	def psm_tmy(self):
		route = 'api/nsrdb_api/solar/nsrdb_psm3_tmy_download.csv'
		self.request_url = self.create_url(route)
		print(self.request_url)
		print(self.params)
		resp = requests.get(self.request_url, params=self.params)
		print(resp.text)
		pass

	#SUNY international
	def suny(self):
		route = 'api/solar/suny_india_download.csv'
		self.request_url = self.create_url(route)
		pass

	#spectral tmy
	def spectral_tmy(self):
		route = 'api/nsrdb_api/solar/spectral_tmy_india_download.csv'
		self.request_url = self.create_url(route)
		pass

if __name__ == '__main__':
	NSRBD('psm_tmy',-99.49218,43.83452,'tdy-2017')
	pass

#https://developer.nrel.gov/api/alt-fuel-stations/v1.json?fuel_type=E85,ELEC&state=CA&limit=2&api_key=rnvNJxNENljf60SBKGxkGVwkXls4IAKs1M8uZl56&format=JSON