'''
Backend for fire map work.
'''

import multiprocessing, time
from flask import Flask, redirect
import json
from omf.weather import getSubGridData

app = Flask(__name__)

@app.route('/')
def root():
	return open('satellitemap_editablePopup.html').read()

@app.route('/test')
def test():
	x = 1 + 2
	return '<b>bold world</b> ' + str(x)

@app.route('/firedata/<lat>/<lon>/<distLat>/<distLon>/<resolution>')
def firedata(lat, lon, distLat, distLon, resolution):
	print(lat, lon, distLat, distLon, resolution)
	x = getSubGridData(str(lat), str(lon), str(distLat), str(distLon), str(resolution))
	# print (json.dumps(x))
	# print(type(json.dumps(x))) # json.dumps is a string
	# print (type(x)) # x is a python dictionary 
	return json.dumps(x) 

@app.route('/circuit.geojson')
def geojson():
	return open('circuit.geojson').read()

@app.route('/L.KML.js')
def kml_lib():
	return open('L.KML.js').read()

if __name__ == '__main__':
	app.run(debug=True)
