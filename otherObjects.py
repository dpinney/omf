#!/usr/bin/env python

import os
import json

def listAllConversions():
	if 'conversions' not in os.listdir('.'):
		os.mkdir('conversions')
	return os.listdir('conversions')

def listAllWeather():
	if 'tmy2s' not in os.listdir('.'):
		os.mkdir('tmy2s')
	return os.listdir('tmy2s')

def listAllComponents():
	if 'components' not in os.listdir('.'):
		os.mkdir('components')
	return os.listdir('components')

def getAllComponents():
	compFiles = listAllComponents()
	components = {}
	for fileName in compFiles:
		with open('./components/' + fileName,'r') as compFile:
			components[fileName.replace('.json','')] = json.load(compFile)
	return components