import json, os, shutil, math, tempfile, random, webbrowser, platform, csv
from pathlib import Path
from os.path import join as pJoin
from pyproj import Proj, transform, Transformer
import requests
import networkx as nx
import numpy as np
from scipy.spatial import ConvexHull
from sklearn.cluster import KMeans
from jinja2 import Template
from flask import Flask, send_file, render_template
from matplotlib import pyplot as plt

import omf
from omf import feeder
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

import pandas as pd

def dssCoords_to_dict(pathToDssFile):
	# Function for taking a .dss (openDSS) file and reading the values into a spreadsheet
	coords_dict = {}
	with open(pathToDssFile, "r+") as inFile:
		allLines = inFile.readlines()
		for line in allLines:
			line_arr = line.split()
			if line_arr[0] == "setbusxy":
				name_str = line_arr[1].split('=')[1]
				x_str = line_arr[2]
				y_str = line_arr[3]
				x_coord = float(x_str.split('=')[1])
				y_coord = float(y_str.split('=')[1])
				coords_dict[name_str] = {'x': x_coord, 'y': y_coord}
	return coords_dict

def coordsFile_to_spreadsheet(pathToInputFile, pathToOutputFile):
	# Function for taking a .txt file containing just the coordinates portion of an openDSS file and reading the values into a spreadsheet
	coords_dict = {}
	with open(pathToInputFile, "r") as inFile:
		allLines = inFile.readlines()
		for line in allLines:
			line_arr = line.split()
			name_str = line_arr[1].split('=')[1]
			x_str = line_arr[2]
			y_str = line_arr[3]
			x_coord = float(x_str.split('=')[1])
			y_coord = float(y_str.split('=')[1])
			coords_dict[name_str] = {'x': x_coord, 'y': y_coord}
	df = pd.DataFrame(data=coords_dict, index=[0])
	df = (df.T)
	print(df)
	df.to_excel(pathToOutputFile)

def feetToDegrees(coordinatesDict, xBase, yBase):
	ft_deg_ratio = 0.000003
	newCoordsDict = {}
	defaultX = None
	defaultY = None
	needsCoordsList = []
	for bus_name in coordinatesDict:
		xVal = coordinatesDict[bus_name]['x']
		yVal = coordinatesDict[bus_name]['y']
		# set the default value in the case of an unentered (0,0) set of coordinates
		if (defaultX is None) or (defaultY is None):
			if (xVal != 0.0) and (yVal != 0.0):
				defaultX = xVal
				defaultY = yVal
				for needy_bus in needsCoordsList:
					newCoordsDict[needy_bus] = {'x': defaultX, 'y': defaultY, 'xDif': 0.0, 'yDif': 0.0, 'xAdj': xBase, 'yAdj': yBase}
					needsCoordsList.remove(needy_bus)
				newCoordsDict[bus_name] = {'x': xVal, 'y': yVal, 'xDif': 0.0, 'yDif': 0.0, 'xAdj': xBase, 'yAdj': yBase}
			else:
				needsCoordsList.append(bus_name)
		else:
			if (xVal != 0.0) and (yVal != 0.0):
				xDif = xVal - defaultX
				yDif = yVal - defaultY
				lonVal = xBase + (xDif * ft_deg_ratio)
				latVal = yBase + (yDif * ft_deg_ratio)
				newCoordsDict[bus_name] = {'x': xVal, 'y': yVal, 'xDif': xDif, 'yDif': yDif, 'xAdj': lonVal, 'yAdj': latVal}
			else:
				newCoordsDict[bus_name] = {'x': defaultX, 'y': defaultY, 'xDif': 0.0, 'yDif': 0.0, 'xAdj': xBase, 'yAdj': yBase}
	return newCoordsDict


def dssCoords_to_spreadsheet(pathToInputFile, pathToOutputFile, xBase, yBase, coordsFormat):
	# Function for taking a .dss (openDSS) file and reading the values into a .csv file
	coords_dict = dssCoords_to_dict(pathToInputFile)
	with open(pathToOutputFile, 'w+') as outFile:
		writer = csv.writer(outFile)
		writer.writerow(["xBase", "yBase"])
		writer.writerow([xBase, yBase])
		writer.writerow(["Bus Name", "xVal", "yVal", "xDif", "yDif", "xAdj", "yAdj"])
		newCoordsDict = {}
		if coordsFormat == "ft":
			newCoordsDict = feetToDegrees(coords_dict, xBase, yBase)
		for bus_name in coords_dict:
			xVal = newCoordsDict[bus_name]["x"]
			yVal = newCoordsDict[bus_name]["y"]
			xDif = newCoordsDict[bus_name]["xDif"]
			yDif = newCoordsDict[bus_name]["yDif"]
			xAdj = newCoordsDict[bus_name]["xAdj"]
			yAdj = newCoordsDict[bus_name]["yAdj"]
			writer.writerow([bus_name, xVal, yVal, xDif, yDif, xAdj, yAdj])
	

def cleanCoordsDss(pathToDssInputFile, pathToCsvCoordsFile, pathToDssOutputFile):
	# Takes in the original openDSS file and csv file with correct coordinates information and writes a new openDSS file with correct lat/lons 
	print("work in progress")
		
def _test():
	lon_orig = -84.946092
	lat_orig = 30.134247
	coordsFormat = "ft"
	dssInputFile = pJoin(__neoMetaModel__._omfDir, 'solvers', 'opendss', 'ieee8500-unbal_no_fuses.clean_reduced.dss')
	csvCoordsFile = pJoin(__neoMetaModel__._omfDir, 'scratch', 'RONM', 'ieee8500-unbal_no_fuses.clean_reduced.coords.csv')
	dssOutputFile = pJoin(__neoMetaModel__._omfDir, 'scratch', 'RONM', 'ieee8500-unbal_no_fuses.clean_reduced.good_coords.csv')
	dssCoords_to_spreadsheet(dssInputFile, csvCoordsFile, lon_orig, lat_orig, coordsFormat)
	# cleanCoordsDss(dssInputFile, csvCoordsFile, dssOutputFile)


if __name__ == '__main__':
	_test()