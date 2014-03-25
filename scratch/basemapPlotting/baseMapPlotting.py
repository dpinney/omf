''' Draw America, also data. '''

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import maskoceans
from random import uniform, choice
import csv, urllib

def baseMapSetup():
	# Set up chart.
	fig = plt.figure()
	m = Basemap(projection='merc',
				lon_0=-95,
				lat_0=35,
				llcrnrlat=20,
				urcrnrlat=50,
				llcrnrlon=-130,
				urcrnrlon=-60,
				rsphere=6371200.,
				resolution='l',
				area_thresh=10000)
	m.drawcoastlines()
	m.drawstates()
	m.drawcountries()
	return m

def addOsmImage():
	# Getting image from OSM to show map features. 
	m = baseMapSetup()
	fname, headers = urllib.urlretrieve('http://render.openstreetmap.org/cgi-bin/export?bbox=-80.05067825317383,38.39379044654673,-79.96004104614258,38.4377914419658&scale=27116&format=png', filename='test.png')
	print 'Downloaded file:', fname
	im = plt.imread(fname)
	m.imshow(interpolation='lanczos', origin='upper')
	#TODO: make the lat/lon coordinates agree. Because clearly the current behavior is wacky.

def testPlots():
	# Hello Basemap Plots
	m = baseMapSetup()
	randPoints = [(uniform(-130,-60),uniform(20,50),uniform(5,45),choice(['red','blue','green'])) for x in range(90)]
	lons = [p[0] for p in randPoints]
	lats = [p[1] for p in randPoints]
	sizes = [p[2] for p in randPoints]
	colors = [p[3] for p in randPoints]
	# Try a scatter plot
	m.scatter(lons, lats, latlon=True, c=colors, s=sizes)
	# Try a mesh
	m.pcolor(lons, lats, sizes, latlon=True, tri=True)

def tmy2Scatter():
	# Try a TMY2 Scatter Plot.
	m = baseMapSetup()
	from tmy2Wrangling import points
	lons = [p[0] for p in points]
	lats = [p[1] for p in points]
	sizes = [p[2] for p in points]
	m.scatter(lons, lats, latlon=True, c='red', s=sizes)

def readNsol():
	# Take in nsol Data, don't chart anything.
	nsolData = []
	with open('nsolOutputsWithInsolation.csv', 'r') as csvFile:
		read = csv.reader(csvFile, quoting=csv.QUOTE_NONNUMERIC)
		for row in read:
			nsolData.append(row)
	headers = nsolData[0]
	table = [dict(zip(headers,row)) for row in nsolData[1:]]
	return table

def nsolScatter():
	# TMY2 stations sized by PV output estimates.
	m = baseMapSetup()
	nsolTable = readNsol()
	lons = [p['LonW'] for p in nsolTable]
	lats = [p['LatN'] for p in nsolTable]
	sizes = [p['ArrayOutput'] for p in nsolTable]
	m.scatter(lons, lats, latlon=True, c='gold', s=sizes)

def nsolMesh():
	# TMY2 stations colored w/ mesh by PV output estimates.
	m = baseMapSetup()
	nsolTable = readNsol()
	lons = [p['LonW'] for p in nsolTable]
	lats = [p['LatN'] for p in nsolTable]
	sizes = [p['ArrayOutput'] for p in nsolTable]
	m.pcolor(lons, lats, sizes, latlon=True, tri=True)

def nsolLots():
	''' Compare nSol estimates to insolation. '''
	# Read the data first:
	nsolTable = readNsol()
	lons = [p['LonW'] for p in nsolTable]
	lats = [p['LatN'] for p in nsolTable]
	sizes = [p['ArrayOutput'] for p in nsolTable]
	insolSizes = [p['TotalAnnualInsolation'] for p in nsolTable]
	bmOptions = {'projection':'merc', 'lon_0':-95, 'lat_0':35, 'llcrnrlat':20, 'urcrnrlat':50,
		'llcrnrlon':-130, 'urcrnrlon':-60, 'rsphere':6371200., 'resolution':'l', 'area_thresh':10000}
	# First Plot
	plt.subplot(211)
	m1 = Basemap(**bmOptions)
	m1.drawcoastlines()
	m1.drawstates()
	m1.drawcountries()
	plt.title('Panel Output')
	mesh1 = m1.pcolor(lons, lats, sizes, latlon=True, tri=True)
	cbar1 = m1.colorbar(mesh1,location='right',pad='5%')
	cbar1.set_label('kWh')
	# Second Plot
	plt.subplot(212)
	m2 = Basemap(**bmOptions)
	m2.drawcoastlines()
	m2.drawstates()
	m2.drawcountries()
	plt.title('Annual Insolation')
	mesh2 = m2.pcolor(lons, lats, insolSizes, latlon=True, tri=True)
	cbar2 = m2.colorbar(mesh2,location='right',pad='5%')
	cbar2.set_label('kWh/m^2')

if __name__ == '__main__':
	nsolLots()
	plt.show()