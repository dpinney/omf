#Easy Solar
"""

Runs easySolar prediction of DHi from GHI

Params:
{Year, USCRN Location}



"""
#Imports
import os
import pandas as pd
import numpy as np
import math
import requests
import datetime
import pysolar
import pytz
from joblib import dump, load

from sklearn.preprocessing import PolynomialFeatures

from weather import pullUscrn

#Import model
clf_log_poly = load('Log_Polynomial_clf.joblib')

#darksky key
_key = '31dac4830187f562147a946529516a8d'
_key2 = os.environ.get('DARKSKY','')

#Station_Dict

Station_Dict = {
	"AK_Cordova_14_ESE":(60.473, -145.35,'US/Alaska'),
	"AK_Deadhorse_3_S":(70.161,-148.46,'US/Alaska'),
	"AK_Denali_27_N":(63.451,-150.87,'US/Alaska'),
	"AK_Fairbanks_11_NE":(64.973,-147.51,'US/Alaska'),
	"AK_Glennallen_64_N":(63.029,-145.50,'US/Alaska'),
	"AK_Gustavus_2_NE":(58.429,-135.69,'US/Alaska'),
	"AK_Ivotuk_1_NNE":(68.484,-155.75,'US/Alaska'),
	"AK_Kenai_29_ENE":(60.723,-150.44,'US/Alaska'),
	"AK_King_Salmon_42_SE":(58.207,-155.92,'US/Alaska'),
	"AK_Metlakatla_6_S":(55.045,-131.58,'US/Alaska'),
	"AK_Port_Alsworth_1_SW":(60.195,-154.31,'US/Alaska'),
	"AK_Red_Dog_Mine_3_SSW":(68.027,-162.92,'US/Alaska'),
	"AK_Ruby_44_ESE":(64.501,-154.12,'US/Alaska'),
	"AK_Sand_Point_1_ENE":(55.347,-160.46,'US/Alaska'),
	"AK_Selawik_28_E":(66.561,-159.00,'US/Alaska'),
	"AK_Sitka_1_NE":(57.057,-135.32,'US/Alaska'),
	"AK_St._Paul_4_NE":(57.157,-170.21,'US/Alaska'),
	"AK_Tok_70_SE":(62.736,-141.20,'US/Alaska'),
	"AK_Toolik_Lake_5_ENE":(68.648,-149.39,'US/Alaska'),
	"AK_Yakutat_3_SSE":(59.508,-139.68,'US/Alaska'),
	"AL_Brewton_3_NNE":(31.144,-87.05,'US/Central'),
	"AL_Clanton_2_NE":(32.851,-86.61,'US/Central'),
	"AL_Courtland_2_WSW":(34.660,-87.34,'US/Central'),
	"AL_Cullman_3_ENE":(34.195,-86.79,'US/Central'),
	"AL_Fairhope_3_NE":(30.548,-87.87,'US/Central'),
	"AL_Gadsden_19_N":(34.285,-85.96,'US/Central'),
	"AL_Gainesville_2_NE":(32.836,-88.13,'US/Central'),
	"AL_Greensboro_2_WNW":(32.716,-87.62,'US/Central'),
	"AL_Highland_Home_2_S":(31.915,-86.31,'US/Central'),
	"AL_Muscle_Shoals_2_N":(34.772,-87.64,'US/Central'),
	"AL_Northport_2_S":(33.212,-87.59,'US/Central'),
	"AL_Russellville_4_SSE":(34.453,-87.71,'US/Central'),
	"AL_Scottsboro_2_NE":(34.693,-86.00,'US/Central'),
	"AL_Selma_6_SSE":(32.456,-87.24,'US/Central'),
	"AL_Selma_13_WNW":(32.335,-86.97,'US/Central'),
	"AL_Talladega_10_NNE":(33.571,-86.05,'US/Central'),
	"AL_Thomasville_2_S":(31.881,-87.73,'US/Central'),
	"AL_Troy_2_W":(31.789,-86.00,'US/Central'),
	"AL_Valley_Head_1_SSW":(34.565,-85.61,'US/Central'),
	"AR_Batesville_8_WNW":(35.820,-91.78,'US/Central'),
	"AZ_Elgin_5_S":(31.590,-110.50,'US/Mountain'),
	"AZ_Tucson_11_W":(32.239,-111.16,'US/Mountain'),
	"AZ_Williams_35_NNW":(35.755,-112.33,'US/Mountain'),
	"AZ_Yuma_27_ENE":(32.834,-114.18,'US/Mountain'),
	"CA_Bodega_6_WSW":(38.320,-123.07,'US/Pacific'),
	"CA_Fallbrook_5_NE":(33.438,-117.19,'US/Pacific'),
	"CA_Merced_23_WSW":(37.237,-120.88,'US/Pacific'),
	"CA_Redding_12_WNW":(40.650,-122.60,'US/Pacific'),
	"CA_Santa_Barbara_11_W":(34.413,-119.87,'US/Pacific'),
	"CA_Stovepipe_Wells_1_SW":(36.601,-117.14,'US/Pacific'),
	"CA_Yosemite_Village_12_W":(37.759,-119.82,'US/Pacific'),
	"CO_Boulder_14_W":(40.035,-105.54,'US/Mountain'),
	"CO_Cortez_8_SE":(37.255,-108.50,'US/Mountain'),
	"CO_Dinosaur_2_E":(40.244,-108.96,'US/Mountain'),
	"CO_La_Junta_17_WSW":(37.863,-103.82,'US/Mountain'),
	"CO_Montrose_11_ENE":(38.543,-107.69,'US/Mountain'),
	"CO_Nunn_7_NNE":(40.806,-104.75,'US/Mountain'),
	"FL_Everglades_City_5_NE":(25.899,-81.31,'US/Eastern'),
	"FL_Sebring_23_SSE":(27.152,-81.36,'US/Eastern'),
	"FL_Titusville_7_E":(28.615,-80.69,'US/Eastern'),
	"GA_Brunswick_23_S":(30.807,-81.45,'US/Eastern'),
	"GA_Newton_8_W":(31.312,-84.47,'US/Eastern'),
	"GA_Newton_11_SW":(31.192,-84.44,'US/Eastern'),
	"GA_Watkinsville_5_SSE":(33.783,-83.38,'US/Eastern'),
	"HI_Hilo_5_S":(None, None,None),
	"HI_Mauna_Loa_5_NNE":(None,None,None),
	"IA_Des_Moines_17_E":(41.556,-93.28,'US/Central'),
	"ID_Arco_17_SW":(43.461,-113.55,'US/Mountain'),
	"ID_Murphy_10_W":(43.204,-116.75, 'US/Mountain'),
	"IL_Champaign_9_SW":(40.052,-88.37,'US/Central'),
	"IL_Shabbona_5_NNE":(41.842,-88.85, 'US/Central'),
	"IN_Bedford_5_WNW":(38.888,-86.5, 'US/Central'),
	"KS_Manhattan_6_SSW":(39.102,-96.61, 'US/Central'),
	"KS_Oakley_19_SSW":(38.870,-100.96, 'US/Central'),
	"KY_Bowling_Green_21_NNE":(37.250,-86.23,'US/Eastern'),
	"KY_Versailles_3_NNW":(38.094,-84.74,'US/Eastern'),
	"LA_Lafayette_13_SE":(30.091,-91.87,'US/Central'),
	"LA_Monroe_26_N":(32.883,-92.11,'US/Central'),
	"ME_Limestone_4_NNW":(46.960,-67.88,'US/Eastern'),
	"ME_Old_Town_2_W":(44.928,-68.70, 'US/Eastern'),
	"MI_Chatham_1_SE":(46.334,-86.92,'US/Michigan'),
	"MI_Gaylord_9_SSW":(46.334,-86.92, 'US/Michigan'),
	"MN_Goodridge_12_NNW":(48.305,-95.87,'US/Central'),
	"MN_Sandstone_6_W":(46.113,-92.99, 'US/Central'),
	"MO_Chillicothe_22_ENE":(39.866,-93.14,'US/Central'),
	"MO_Joplin_24_N":(37.427,-94.58,'US/Central'),
	"MO_Salem_10_W":(37.634,-91.72, 'US/Central'),
	"MS_Holly_Springs_4_N":(34.822,-89.43, 'US/Central'),
	"MS_Newton_5_ENE":(32.337,-89.07, 'US/Central'),
	"MT_Dillon_18_WSW":(45.158,-113.00, 'US/Mountain'),
	"MT_Lewistown_42_WSW":(46.884,-110.28,'US/Mountain'),
	"MT_St._Mary_1_SSW":(48.741,-113.43,'US/Mountain'),
	"MT_Wolf_Point_29_ENE":(48.308,-105.10,'US/Mountain'),
	"MT_Wolf_Point_34_NE":(48.488,-105.20,'US/Mountain'),
	"NC_Asheville_8_SSW":(35.494,-82.61,'US/Eastern'),
	"NC_Asheville_13_S":(35.418,-82.55,'US/Eastern'),
	"NC_Durham_11_W":(35.970,-79.09,'US/Eastern'),
	"ND_Jamestown_38_WSW":(46.770,-99.47, 'US/Central'),
	"ND_Medora_7_E":(46.894,-103.37,'US/Central'),
	"ND_Northgate_5_ESE":(48.967,-102.17,'US/Central'),
	"NE_Harrison_20_SSE":(42.424,-103.73,'US/Eastern'),
	"NE_Lincoln_8_ENE":(40.848,-96.56,'US/Eastern'),
	"NE_Lincoln_11_SW":(40.695,-96.85,'US/Eastern'),
	"NE_Whitman_5_ENE":(42.067,-101.44,'US/Eastern'),
	"NH_Durham_2_N":(43.171,-70.92,'US/Eastern'),
	"NH_Durham_2_SSW":(43.108,-70.94,'US/Eastern'),
	"NM_Las_Cruces_20_N":(32.613,-106.74,'US/Mountain'),
	"NM_Los_Alamos_13_W":(35.858,-106.52,'US/Mountain'),
	"NM_Socorro_20_N":(34.355,-106.88,'US/Mountain'),
	"NV_Baker_5_W":(39.011,-114.20, 'US/Pacific'),
	"NV_Denio_52_WSW":(41.848,-119.63,'US/Pacific'),
	"NV_Mercury_3_SSW":(36.623,-116.02,'US/Pacific'),
	"NY_Ithaca_13_E":(42.440,-76.24,'US/Eastern'),
	"NY_Millbrook_3_W":(42.440,-76.24,'US/Eastern'),
	"OH_Wooster_3_SSE":(40.763,-81.91, 'US/Eastern'),
	"OK_Goodwell_2_E":(36.599,-101.59, 'US/Central'),
	"OK_Goodwell_2_SE":(36.568,-101.60,'US/Central'),
	"OK_Stillwater_2_W":(36.118,-97.09,'US/Central'),
	"OK_Stillwater_5_WNW":(36.134,-97.10,'US/Central'),
	"ON_Egbert_1_W":(44.232,-79.78, 'US/Eastern'),
	"OR_Coos_Bay_8_SW":(43.271,-124.31, 'US/Pacific'),
	"OR_Corvallis_10_SSW":(44.418,-123.32,'US/Pacific'),
	"OR_John_Day_35_WNW":(44.555,-119.64,'US/Pacific'),
	"OR_Riley_10_WSW":(43.471,-119.69,'US/Pacific'),
	"PA_Avondale_2_N":(39.859,-75.78,'US/Eastern'),
	"RI_Kingston_1_NW":(41.490,-71.54,'US/Eastern'),
	"RI_Kingston_1_W":(41.478,-71.54,'US/Eastern'),
	"SA_Tiksi_4_SSE":(None,None,None),
	"SC_Blackville_3_W":(33.355,-81.32,'US/Eastern'),
	"SC_McClellanville_7_NE":(33.153,-79.36,'US/Eastern'),
	"SD_Aberdeen_35_WNW":(45.711,-99.12, 'US/Central'),
	"SD_Buffalo_13_ESE":(45.515,-103.30,'US/Central'),
	"SD_Pierre_24_S":(44.019,-100.35,'US/Central'),
	"SD_Sioux_Falls_14_NNE":(43.734,-96.62,'US/Central'),
	"TN_Crossville_7_NW":(36.013,-85.13,'US/Eastern'),
	"TX_Austin_33_NW":(30.621,-98.08,'US/Central'),
	"TX_Bronte_11_NNE":(32.040,-100.24,'US/Central'),
	"TX_Edinburg_17_NNE":(26.525,-98.06,'US/Central'),
	"TX_Monahans_6_ENE":(31.621,-102.80,'US/Central'),
	"TX_Muleshoe_19_S":(33.955,-102.77,'US/Central'),
	"TX_Palestine_6_WNW":(31.779,-95.72,'US/Central'),
	"TX_Panther_Junction_2_N":(29.348,-103.20,'US/Central'),
	"TX_Port_Aransas_32_NNE":(28.304,-96.82,'US/Central'),
	"UT_Brigham_City_28_WNW":(41.616,-112.54,'US/Mountain'),
	"UT_Torrey_7_E":(38.302,-111.29, 'US/Mountain'),
	"VA_Cape_Charles_5_ENE":(37.290,-75.92, 'US/Eastern'),
	"VA_Charlottesville_2_SSE":(37.997,-78.46, 'US/Eastern'),
	"WA_Darrington_21_NNE":(48.540,-121.44, 'US/Pacific'),
	"WA_Quinault_4_NE":(47.513,-123.81,'US/Pacific'),
	"WA_Spokane_17_SSW":(47.417,-117.52,'US/Pacific'),
	"WI_Necedah_5_WNW":(44.060,-90.17, 'US/Central'),
	"WV_Elkins_21_ENE":(39.012,-79.47, 'US/Eastern'),
	"WY_Lander_11_SSE":(42.675,-108.66, 'US/Mountain'),
	"WY_Moose_1_NNE":(43.661,-110.71, 'US/Mountain'),
	"WY_Sundance_8_NNW":(44.516,-104.43, 'US/Mountain')
}



def _getUscrnData(year='2020', location='TX_Austin_33_NW', dataType="SOLARAD"):
	ghiData = pullUscrn(year, location, dataType)
	return ghiData

#Standard positional arguments are for TX_Austin
def _getDarkSkyCloudCoverForYear(year='2020', lat=30.581736, lon=-98.024098, key=_key, units='si'):
	cloudCoverByHour = {}
	coords = '%0.2f,%0.2f' % (lat, lon)
	times = list(pd.date_range('{}-01-01'.format(year), '{}-12-31'.format(year), freq='D'))
	while times:
		time = times.pop(0)
		print(time)
		url = 'https://api.darksky.net/forecast/%s/%s,%s?exclude=daily,alerts,minutely,currently&units=%s' % (key, coords, time.isoformat(), units ) 
		res = requests.get(url).json()
		try:
			dayData = res['hourly']['data']
		except KeyError:
			print("No day data!!!!!!")
			continue
		for hour in dayData:
			try:
				cloudCoverByHour[hour['time']] = hour['cloudCover']
			except KeyError:
				print("No Cloud Cover Data")
				pass
	return cloudCoverByHour

def _makeDataNonzero(data):
	ghiData=list(filter(lambda num: num!=0.0, data))
	assert(all(x[0]!=0 for x in ghiData))
	return ghiData

def _logifyData(data):
	data = np.log(data)
	return data

def _initPolyModel(X, degrees=5):
    poly = PolynomialFeatures(degree=degrees)
    _X_poly = poly.fit_transform(X)
    return _X_poly

def getCosineOfSolarZenith(lat, lon, datetime, timezone):
	date = pytz.timezone(timezone).localize(datetime)
	solar_altitude = pysolar.solar.get_altitude(lat,lon,date)
	solar_zenith = 90 - solar_altitude
	cosOfSolarZenith = math.cos(math.radians(solar_zenith))
	return cosOfSolarZenith

def preparePredictionVectors(year='2020', lat=30.581736, lon=-98.024098, station='TX_Austin_33_NW', timezone='US/Central'):
	cloudCoverData = _getDarkSkyCloudCoverForYear(year, lat, lon)
	ghiData = _getUscrnData(year, station, dataType="SOLARAD")
	#for each 8760 hourly time slots, make a timestamp for each slot, look up cloud cover by that slot
	#then append cloud cover and GHI reading together
	start_time = datetime.datetime(int(year),1,1,0)
	cosArray = []
	input_array = []
	for i in range(len(ghiData)): #Because ghiData is leneth 8760, one for each hour of a year
		time = start_time + datetime.timedelta(minutes=60*i)
		tstamp = int(datetime.datetime.timestamp(time))
		try:
			cloudCover = cloudCoverData[tstamp]
		except KeyError:
			cloudCover = 0
		#I have my cloud cover, iterate over my ghi and cosine arrays
		cosOfSolarZenith = getCosineOfSolarZenith(lat, lon, time, timezone)
		ghi = ghiData[i]
		if ghi <= 0:
			#Not most efficient logic but....
			#Still need to decide how to handle zero vals. Test this
			input_array.append((0, cloudCover))
		else:	
			ghi = np.log(ghi)
			input_array.append((ghi, cloudCover))
		cosArray.append(cosOfSolarZenith)
	return input_array, ghiData, cosArray


def predictPolynomial(X, model, degrees=5):
	X = _initPolyModel(X, degrees=5)
	predictions_dhi = model.predict(X)
	return predictions_dhi

def get_synth_dhi_dni(uscrn_station, year):
	print("********EASY SOLAR STARTED************")
	lat = Station_Dict[uscrn_station][0]
	lon = Station_Dict[uscrn_station][1]
	timezone = Station_Dict[uscrn_station][2]
	input_array, ghiData, cosArray = preparePredictionVectors(year, lat, lon, uscrn_station, timezone)
	log_prediction = predictPolynomial(input_array, clf_log_poly)
	dhiPredictions = np.exp(log_prediction)
	dniXCosTheta = ghiData - dhiPredictions #This is cos(theta) * DNI
	dni_array = ([dniXCosTheta[i]/cosArray[i] for i in range(len(dniXCosTheta))]) 
	result = list(zip(dhiPredictions, ghiData, dni_array))
	return result

def easy_solar_tests(uscrn_station='TX_Austin_33_NW'):
	print("********EASY SOLAR TEST STARTED************")
	print(Station_Dict)
	year='2018'
	lat = Station_Dict[uscrn_station][0]
	lon = Station_Dict[uscrn_station][1]
	timezone = Station_Dict[uscrn_station][2]
	input_array, ghiData, cosArray = preparePredictionVectors(year, lat, lon, uscrn_station, timezone)
	assert len(input_array) == len(ghiData) == len(cosArray)
	log_prediction = predictPolynomial(input_array, clf_log_poly)
	dhiPredictions = np.exp(log_prediction)
	dniXCosTheta = ghiData - dhiPredictions #This is cos(theta) * DNI
	dni_array = ([dniXCosTheta[i]/cosArray[i] for i in range(len(dniXCosTheta))]) 
	result = list(zip(dhiPredictions, ghiData, dni_array))
	assert 	len(result) == len(input_array)
	print(result)

if __name__ == '__main__':
	easy_solar_tests()
	# print(get_synth_dhi_dni("VA_Charlottesville_2_SSE",'2018'))
