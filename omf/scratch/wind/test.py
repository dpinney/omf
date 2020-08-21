import multiprocessing, time
from flask import Flask
import json
from omf.weather import getSubGridData

lat = 40.758701
lon = -111.876183
dist = 20
resolution = 20
x = getSubGridData(str(lat), str(lon), str(dist), str(dist), str(resolution))
print (x['dwml']['data']['parameters'][0]['fire-weather']['value'][0])