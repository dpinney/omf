from __future__ import print_function
import json
import time
import datetime
import csv

#See original scraping code here: https://github.com/akrherz/iem/blob/master/scripts/asos/iem_scraper_example.py

# Python 2 and 3: alternative 4
try:
    from urllib.request import urlopen
except ImportError:
	from urllib2 import urlopen

def get_stations_from_networks():
    """Build a station list by using a bunch of IEM networks."""
    stations = []
    states = """AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME
     MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT
     WA WI WV WY"""
    networks = []
    for state in states.split():
        networks.append("%s_ASOS" % (state,))
    with open('asosStationTable.csv', 'wb') as csvfile:
    	fieldnames = ['Station Id', 'Station Name', 'County', 'State', 'Latitude', 'Longitude', 'Elevation', 'Time Zone']
    	csvwriter = csv.DictWriter(csvfile, delimiter=',', fieldnames=fieldnames)
    	for network in networks:
			current = []
			current.append(network)
			uri = ("https://mesonet.agron.iastate.edu/"
			"geojson/network/%s.geojson") % (network,)
			data = urlopen(uri)
			jdict = json.load(data)
			#map attribute to entry in csv
			csvwriter.writeheader()
			for site in jdict['features']:
				currentSite = {}
				currentSite['Station Id'] = site['properties']['sid']
				currentSite['Station Name'] = site['properties']['sname']
				currentSite['County'] = site['properties']['county']
				currentSite['State'] = site['properties']['state']
				currentSite['Latitude'] = site['geometry']['coordinates'][0]
				currentSite['Longitude'] = site['geometry']['coordinates'][1]
				currentSite['Elevation'] = site['properties']['elevation']
				currentSite['Time Zone'] = site['properties']['tzname']
				csvwriter.writerow(currentSite)

	return stations

if __name__ == '__main__':
	get_stations_from_networks()