#!/bin/python

import flask
import CVRgrapher
app = flask.Flask(__name__)

@app.route('/')

def root():
	CVRgrapher.buildGraph()
	testPng = flask.url_for('static',filename='test.png')
	return '<img src="' + testPng + '"/>'

# This will run on all interface IPs.
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug='False')