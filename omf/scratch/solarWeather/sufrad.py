import urllib2
import json
import csv

def getSurfradSites():
	url = 'ftp://aftp.cmdl.noaa.gov/data/radiation/surfrad/'
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	sitesRaw = response.read()
	siteLines = sitesRaw.split('\r\n')
	return [x[56:] for x in siteLines if '_' in x and '->' not in x]

def getRadiationYears(radiation_type, site, year):
	URL = 'ftp://aftp.cmdl.noaa.gov/data/radiation/{}/{}/{}/'.format(radiation_type, site, year)
	#FILE = 'tbl19001.dat' - example
	# Get directory contents.
	dirReq = urllib2.Request(URL)
	dirRes = urllib2.urlopen(dirReq)
	dirLines = dirRes.read().split('\r\n')
	allFileNames = [x[56:] for x in dirLines if x!='']
	accum = []
	for fName in allFileNames:
		req = urllib2.Request(URL + fName)
		response = urllib2.urlopen(req)
		page = response.read()
		lines = page.split('\n')
		siteName = lines[0]
		latLonVersion = lines[1].split()
		data = [x.split() for x in lines[2:]]
		minuteIntervals = ['0']
		hourlyReads = [x for x in data if len(x) >= 5 and x[5] in minuteIntervals]
		hourlyReadsSub = [
			{
				'col{}'.format(c):row[c] for c in range(len(row))
			}
			for row in hourlyReads
		]
		accum.extend(hourlyReadsSub)
		print('processed file {}'.format(fName))
	return accum

#Create tsv file from dict 
def create_tsv(data, radiation_type, site, year):
	column_count = len(data[0])
	output = csv.DictWriter(open('{}-{}-{}.tsv'.format(radiation_type, site, year), 'w'), fieldnames=['col{}'.format(x) for x in range(column_count)], delimiter='\t')
	for item in data:
	 	output.writerow(item)

'''Get solard or surfrad data. Optional export to csv with out_file option'''
def get_radiation_data(radiation_type, site, year, out_file=None):
	allYears = getRadiationYears(radiation_type, site, year)
	if out_file is not None:
		create_tsv(allYears, radiation_type, site, year)
	else:
		return allYears

get_radiation_data('surfrad', 'Boulder_CO', 2019)
get_radiation_data('solrad', 'bis', 2019)



'''
Surfrad data

====HEADERS====
station_name	character	station name, e. g., Goodwin Creek
latitude		real		latitude in decimal degrees (e. g., 40.80)
longitude		real		longitude in decimal degrees (e. g., 105.12)
elevation		integer		elevation above sea level in meters

====ROWS====
0	year			integer		year, i.e., 1995
1	jday			integer		Julian day (1 through 365 [or 366])
2	month			integer		number of the month (1-12)
3	day				integer		day of the month(1-31)
4	hour			integer		hour of the day (0-23)
5	min				integer		minute of the hour (0-59)
6	dt				real		decimal time (hour.decimalminutes, e.g., 23.5 = 2330)
7	zen				real		solar zenith angle (degrees)
8	dw_solar		real		downwelling global solar (Watts m^-2)
9	uw_solar		real		upwelling global solar (Watts m^-2)
10	direct_n		real		direct-normal solar (Watts m^-2)
11	diffuse			real		downwelling diffuse solar (Watts m^-2)
12	dw_ir			real		downwelling thermal infrared (Watts m^-2)
13	dw_casetemp		real		downwelling IR case temp. (K)
14	dw_dometemp		real		downwelling IR dome temp. (K)
15	uw_ir			real		upwelling thermal infrared (Watts m^-2)
16	uw_casetemp		real		upwelling IR case temp. (K)
17	uw_dometemp		real		upwelling IR dome temp. (K)
18	uvb				real		global UVB (milliWatts m^-2)
19	par				real		photosynthetically active radiation (Watts m^-2)
20	netsolar		real		net solar (dw_solar - uw_solar) (Watts m^-2)
21	netir			real		net infrared (dw_ir - uw_ir) (Watts m^-2)
22	totalnet		real		net radiation (netsolar+netir) (Watts m^-2)
23	temp			real		10-meter air temperature (?C)
24	rh				real		relative humidity (%)
25	windspd			real		wind speed (ms^-1)
26	winddir			real		wind direction (degrees, clockwise from north)
27	pressure		real		station pressure (mb)
'''