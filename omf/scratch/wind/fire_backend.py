'''
Backend for fire map work.
'''

import multiprocessing, time
from flask import Flask, redirect, render_template, send_file
import json
from omf.weather import getSubGridData
import io
import requests

app = Flask(__name__)

@app.route('/')
def root():
	return open('satellitemap_editablePopup.html').read()

@app.route('/getkmz')
def kmz():
    return render_template('satellitemap_editablePopup.html')

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
def circuit():
	return open('circuit.geojson').read()

# @app.route('/L.KML.js')
# def kml_lib():
# 	return open('L.KML.js').read()

@app.route('/my_kmz')
def my_kmz():
	# return open('day1fireotlk.kmz').read()
	url = 'https://www.spc.noaa.gov/products/fire_wx/day1fireotlk.kmz'
	# url = 'https://www.spc.noaa.gov/products/fire_wx/day2fireotlk.kmz'
	# url = 'https://www.spc.noaa.gov/products/fire_wx/day38fireotlk.kmz'
	r = requests.get(url, allow_redirects=True)
	return send_file(r.content,
		# as_attachment = True,
		mimetype="application/vnd",
		)

@app.route('/https://www.spc.noaa.gov/products/fire_wx/day1fireotlk.kmz')
def kmz_address():
	return render_template('https://www.spc.noaa.gov/products/fire_wx/day1fireotlk.kmz')

@app.route('/data.geojson')
def data():
	return open('data.geojson').read()

if __name__ == '__main__':
	app.run(debug=True)
