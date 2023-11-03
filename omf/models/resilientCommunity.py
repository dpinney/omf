''' Calculates Social Vulnerability for a given Circuit '''
import pathlib
import warnings
# warnings.filterwarnings("ignore")
import time
import urllib.request
import shutil, datetime
from os.path import join as pJoin
import webbrowser
import requests
#import zipfile
#import shapefile
import io
from io import BytesIO
import numpy as np
import json
import math
import pandas as pd
#from shapely.geometry import Polygon
#from shapely.geometry import Point
from pyproj import Transformer
#import geopandas as gpd
import matplotlib.colorbar as colorbar
#import matplotlib.colors as clr
import matplotlib.pyplot as plt
#import base64


# OMF imports
from omf import feeder, geo
from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *


# GEO py imports



# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

  
   
                                 
def work(modelDir, inputDict):
    ''' Run the model in its directory. '''
    outData = {}
    #omd_file_path = pJoin(omf.omfDir,'static','publicFeeders', inputDict['inputDataFileName'])
    #geo.map_omd(inputDict['InputFilePath'], modelDir, open_browser=False )
    #geo.map_omd(omd_file_path, modelDir, open_browser=False)
    #outData['resilienceMap'] = open( pJoin( modelDir, "geoJson_offline.html"), 'r' ).read()
    #geojson = pJoin(omf.omfDir,'static','publicFeeders', omdfileName)
    #outData['soviData'] = json.dumps('/Users/davidarmah/Documents/Python/Testing /out.geojson')

  


    return outData
   


def test():
	outData = {}
    #createLegend()
     #omd_file_path = pJoin(omf.omfDir,'static','publicFeeders')
     #print(omd_file_path)
     
def new(modelDir):
	outData = {}
	

@neoMetaModel_test_setup
def _disabled_tests():
	# Location
	modelLoc = pJoin(__neoMetaModel__._omfDir,"data","Model","admin","Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		pass # No previous test results.
	# Create New.
	new(modelLoc)
	# Pre-run.
	__neoMetaModel__.renderAndShow(modelLoc)
	# Run the model.
	__neoMetaModel__.runForeground(modelLoc)
	# Show the output.
	__neoMetaModel__.renderAndShow(modelLoc)

if __name__ == '__main__':
     _disabled_tests()
      #test()
