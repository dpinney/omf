from pyproj import Proj, transform
import webbrowser

# Source: https://github.com/fitnr/stateplane/blob/master/stateplane/dicts.py
# These are NAD83 EPSG identifiers.
# If you need others like NAD27, try https://epsg.io
shortToEpsg = {"AK_1":26931,"AK_2":26932,"AK_3":26933,"AK_4":26934,"AK_5":26935,"AK_6":26936,"AK_7":26937,"AK_8":26938,"AK_9":26939,"AK_10,":26940,"AL_E":26929,"AL_W":26930,"AR_N":26951,"AR_S":26952,"AZ_C":26949,"AZ_E":26948,"AZ_W":26950,"CA_1":26941,"CA_2":26942,"CA_3":26943,"CA_4":26944,"CA_5":26945,"CA_6":26946,"CO_C":26954,"CO_N":26953,"CO_S":26955,"CT":26956,"DE":26957,"FL_E":26958,"FL_N":26960,"FL_W":26959,"GA_E":26966,"GA_W":26967,"HI_1":26961,"HI_2":26962,"HI_3":26963,"HI_4":26964,"HI_5":26965,"IA_N":26975,"IA_S":26976,"ID_C":26969,"ID_E":26968,"ID_W":26970,"IL_E":26971,"IL_W":26972,"IN_E":26973,"IN_W":26974,"KS_N":26977,"KS_S":26978,"KY_N":2205,"KY_S":26980,"LA_N":26981,"LA_S":26982,"MA_I":26987,"MA_M":26986,"MD":26985,"ME_E":26983,"ME_W":26984,"MI_C":26989,"MI_N":26988,"MI_S":26990,"MN_C":26992,"MN_N":26991,"MN_S":26993,"MO_C":26997,"MO_E":26996,"MO_W":26998,"MS_E":26994,"MS_W":26995,"MT":32100,"NC":32119,"ND_N":32120,"ND_S":32121,"NE":32104,"NH":32110,"NJ":32111,"NM_C":32113,"NM_E":32112,"NM_W":32114,"NV_C":32108,"NV_E":32107,"NV_W":32109,"NY_C":32116,"NY_E":32115,"NY_LI":32118,"NY_W":32117,"OH_N":32122,"OH_S":32123,"OK_N":32124,"OK_S":32125,"OR_N":32126,"OR_S":32127,"PA_N":32128,"PA_S":32129,"RI":32130,"SC":32133,"SD_N":32134,"SD_S":32135,"TN":32136,"TX_C":32139,"TX_N":32137,"TX_NC":32138,"TX_S":32141,"TX_SC":32140,"UT_C":32143,"UT_N":32142,"UT_S":32144,"VA_N":32146,"VA_S":32147,"VT":32145,"WA_N":32148,"WA_S":32149,"WI_C":32153,"WI_N":32152,"WI_S":32154,"WV_N":32150,"WV_S":32151,"WY_E":32155,"WY_EC":32156,"WY_W":32158,"WY_WC":32157}

# Reverse above dict to map in the other direction.
epsgToShort = {v: k for k, v in shortToEpsg.items()}

def statePlaneToLatLon(easting, northing, epsg = None):
	if not epsg:
		# Center of the USA default
		epsg = 26978
	inProj = Proj(init = 'EPSG:' + str(epsg), preserve_units = True)
	outProj = Proj(init = 'EPSG:4326')
	lon, lat = transform(inProj, outProj, easting, northing)
	return (lat, lon)

def latLonToStatePlane(lat, lon, epsg = None):
	if not epsg:
		# Center of the USA default
		epsg = 26978
	inProj = Proj(init = 'EPSG:4326')
	outProj = Proj(init = 'EPSG:' + str(epsg), preserve_units = True)
	easting, northing = transform(inProj, outProj, lon, lat)
	return (easting, northing)

def dd2dms(dd):
	'Decimal degress to Degrees/Minutes/Seconds'
	d = int(dd)
	md = abs(dd - d) * 60
	m = int(md)
	sd = (md - m) * 60
	return (d, m, sd)

def dms2dd(degrees, minutes, seconds, direction):
    'Degree/minute/second to decimal degrees'
    dd = float(degrees) + float(minutes)/60 + float(seconds)/(60*60);
    if direction == 'E' or direction == 'N':
        dd *= -1
    return dd;

def decLatLonToLetter(lat, lon):
	"Decimal lat lon to GridLAB-D's weird Degree/Minute/Second format."
	latCode = 'N' if lat > 0 else 'S'
	lonCode = 'E' if lon > 0 else 'W'
	lat_d, lat_m, lat_s = dd2dms(lat)
	lon_d, lon_m, lon_s = dd2dms(lon)
	return (
		str(abs(lat_d)) + latCode + str(lat_m) + ':' + str(lat_s), 
		str(abs(lon_d)) + lonCode + str(lon_m) + ':' + str(lon_s)
	)

def weird2dms(val, sep1, sep2):
	"Handle GridLAB-D's weird Degree/Minute/Second format"
	val_h, val_s = letLat.split(':')
	val_h_split = val_h.split(sep1)
	if len(val_h_split) == 2:
		val_d, val_m = val_h_split
		key = sep1
	else:
		val_d, val_m = val_h.split(sep2)
		key = sep2
	return (val_d, val_m, val_s, key)

def letterLatLonToDec(letLat, letLon):
	"GridLAB-D's weird Degree/Minute/Second format to Decimal lat lon."
	latDd = dms2dd(weird2dms(letLat, 'N', 'S')),
	lonDd = dms2dd(weird2dms(letLon, 'E', 'W'))
	return (latDms, lonDd)

def openInGoogleMaps(lat, lon):
	"Open a browser to the (lat, lon) in Google Maps"
	loc = 'https://www.google.com/maps/place/{}+{}/'.format(lat,lon)
	webbrowser.open_new(loc)

def _tests():
	e, n = 249.2419752733258, 1186.1488466689188
	lat, lon = statePlaneToLatLon(e, n, 2205)
	print (lat, lon) #(37.37267827914456, -89.89482331256504)
	e2, n2 = latLonToStatePlane(lat, lon, epsg=2205)
	print (e2, n2) # (249.24197527189972, 1186.1488466408398)
	letLat, letLon = decLatLonToLetter(lat, lon)
	print (letLat, letLon) # ('37N22:21.6418049204', '89W53:41.3639252341')
	# openInGoogleMaps(lat, lon)

if __name__ == '__main__':
	_tests()