'''
Backend for fire map work.
'''

import multiprocessing, time
from flask import Flask

app = Flask(__name__)

@app.route('/')
def root():
	return 'Hello World!'

@app.route('/test')
def test():
	x = 1 + 2
	return '<b>bold world</b>' + str(x)

@app.route('/firedata/<coords>')
def firedata(coords):
	# x = omf.weather.get_ndfd(33,53)
	return coords

#FRONTEND JAVASCRIPT
# Sending requests from the frontend: https://www.w3schools.com/xml/ajax_xmlhttprequest_send.asp
# Example:
# var xhttp = new XMLHttpRequest();
# xhttp.open("GET", "firedata/33,44", false);
# xhttp.send();
# console.log(xhttp.responseText);

if __name__ == '__main__':
	app.run(debug=True)