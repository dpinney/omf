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
import zipfile
import shapefile
import io
from io import BytesIO
import numpy as np
import json
import math
import pandas as pd
from shapely.geometry import Polygon
from shapely.geometry import Point
from pyproj import Transformer
import geopandas as gpd
import matplotlib.colorbar as colorbar
import matplotlib.colors as clr
import matplotlib.pyplot as plt
import base64


# OMF imports
from omf import feeder, geo
from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *


# GEO py imports



# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

  
# Retrieves necessary data from ZIP File and exports to geojson
# Input: dataURL -> URL to retrieve data from
# returns geojson of census NRI data
def retrieveCensusNRI():
    
    try:
        
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko)  Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
        
        nridataURL = "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Shapefile_CensusTracts/NRI_Shapefile_CensusTracts.zip"
        r = requests.get(nridataURL, headers=hdr)
        z = zipfile.ZipFile(BytesIO(r.content))
        
		# get file names needed to build geoJSON
        shpPath = [x for x in z.namelist() if x.endswith('.shp')][0]
        dbfPath = [x for x in z.namelist() if x.endswith('.dbf')][0]
        prjPath = [x for x in z.namelist() if x.endswith('.prj')][0]
        
        with shapefile.Reader(shp=BytesIO(z.read(shpPath)), 
                      dbf=BytesIO(z.read(dbfPath)), 
                      prj=BytesIO(z.read(prjPath))) as shp:
               geojson_data = shp.__geo_interface__
               prefix = list(pathlib.Path(__file__).parts)
               prefix[7] = 'static'
               prefix[8] = 'testFiles'
               outfile = pathlib.Path(*prefix) / 'census_and_NRI_database_MAR2023.json'
               with open(outfile, 'w') as f:
                     json.dump(geojson_data, f,indent=4)
               return outfile
    except Exception as e:
        print("Error trying to retrieve Census Data as GeoJson")
        print(e)

# Finds Census Tract at a given lon / lat
# Input: lat -> specified latitude value
# Input: lon -> specified longitude value
# return censusTract ->  census Tract found at location
def findCensusTract(lat, lon):
    try:
        request_url = "https://geo.fcc.gov/api/census/block/find?latitude="+str(lat)+"&longitude="+str(lon)+ "&censusYear=2020&format=json"
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        resp = opener.open(request_url)
        censusJson = json.loads(resp.read())
        censusTract = censusJson['Block']['FIPS'][:-4]   
        return  censusTract
    except Exception as e:
        print("Error trying to retrieve tract information from Census API")
        print(e)


# Get Census Tract Social Vulnerability Data
# Input: censusJson -> geoJson data
# Input: tractList -> list of tracts
# return geomData, soviData -> list of geometrys and social vulnerability for tracts found in list
def getSoviData(nrigeoJson, tractList):
    soviData = []
    geomData = []
    headers = list(nrigeoJson['features'][0]['properties'].keys())
    for i in nrigeoJson['features']:
        tractID = i['properties']['TRACTFIPS']
        if tractID in tractList:
            soviData.append([i['properties']['TRACTFIPS'],i['properties']['SOVI_SCORE'],i['properties']['SOVI_RATNG'], i['properties']['SOVI_SPCTL']])
            geom = i['geometry']['coordinates'][0]
            geomData.append(geom)

    return geomData, soviData, headers

# Gets Census Tract data from a specified state
# input: nrigeoJson -> nri geojson
# input stateName -> Specified state name
def getTractDatabyState(nrigeoJson,stateName):
    data = []
    geom = []
    headers = list(nrigeoJson['features'][0]['properties'].keys())
    for i in nrigeoJson['features']:
        state = i['properties']['STATE']
        if state == stateName:
            data.append
            properties = []
            for k in i['properties']:
                properties.append(i['properties'][k])
            data.append(properties)
            geom.append(i['geometry']['coordinates'][0])
    return geom, data, headers


# find census located at specified circuit nodes
# Input:pathToOmd -> path to circuit file
# return censusTracts -> census tract
def getCircuitNRI(pathToOmd):
    censusTracts = []
    with open(pathToOmd) as inFile:
        fullFile = json.load(inFile)
        for i in fullFile['tree']:
             if (fullFile['tree'][i]['object'] == 'node'):
                  node =  fullFile['tree'][i]
                  currTract = findCensusTract(node['latitude'], node['longitude'])
                  if currTract not in censusTracts:
                       censusTracts.append(currTract)
    return censusTracts

# transform coordinates from WGS_1984_Web_Mercator_Auxiliary_Sphere(EPSG 3857) to EPSG:4326
# Input: coordList -> list of coordinates (geometry)
# return coordList -> transformed coordinates
def transform(coordList):
    for idx, i in enumerate(coordList):
        lat,lon = i[0], i[1]
        x = (lat * 180) / 20037508.34
        y = (lon * 180) / 20037508.34
        y = (math.atan(math.pow(math.e, y * (math.pi / 180))) * 360) / math.pi - 90
        coordList[idx] = [x,y]
        
    return coordList

# runs transformations for a list of geometries
# Input: geos -> list of geometry
#return geoTransformed -> transofrmed list of geometries
def runTransformation(geos):
    geoTransformed = []
    for i in geos:
        if (isinstance(i[0][0], float)):
            geoTransformed.append(transform(i)) 
        else:
            geoTransformed.append(transform(i[0]))
    return geoTransformed


# Creates Pandas DF from list of data containing GeoData 
# input: tractData -> Data associated with data
# input: columns -> columns for data
# input: geoTransformed -> EPSG:4326 transformed geometry
def createDF(tractData, columns, geoTransformed):
    data = pd.DataFrame(tractData, columns = columns)
    data['geometry'] = geoTransformed
    return data

# Creates GeoPandas DF From pandas DF
# input: df -> pandas df
# return geo -> geodataframe
def createGeoDF(df):
    df['geometry'] = df['geometry'].apply(Polygon)
    geo = gpd.GeoDataFrame(df, geometry=df["geometry"], crs="EPSG:4326")
    return geo

# creates legend to overlay with map_omd map
def createLegend():
    colors = ["blue", "lightblue", "lightgreen", "yellow", "gray", "black"]
    labels = ['Very High', 'Rel. High', 'Rel. Moderate', 'Rel. Low', 'Very Low', "Data Unavailable"]
    num_colors = len(colors)
    cmap_ = clr.ListedColormap(colors)
    fig = plt.figure()
    ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
    cb = colorbar.ColorbarBase(ax, orientation='horizontal',
                           cmap=cmap_, norm=plt.Normalize(-.3, num_colors - .5))  
    plt.title("Social Vulnerability Legend")
    cb.set_ticks(range(num_colors))
    cb.ax.set_xticklabels(labels)
    path = pJoin(omf.omfDir,'static','testFiles', 'legend.png')

    plt.savefig(path,bbox_inches='tight')

    return path

# Re-runs methods and Updates data 
# input: omd_file -> omd circuit file
def updateData(omd_file):
     
     nrigeoJson = retrieveCensusNRI()
     with open(nrigeoJson) as json_file:
        geoJson = json.load(json_file)
     censusTracts = getCircuitNRI(omd_file)
     geometry, soviData = getSoviData(geoJson, censusTracts)
     transformedGeo = runTransformation(geometry)
     censusDF = createDF(soviData, transformedGeo)
     censusGeoDF = createGeoDF(censusDF)
     censusGeoDF.to_file('./out.geojson', driver='GeoJSON')
     #legend_path = createLegend()
               
# Cooperative Methods

# nriDF -> nri dataframe
# coopDF -> cooperative Dataframe
# tractList -> list of tracts corresponding to the outer borders of cooperative
def findallTracts(nriDF, coopDF, tractlist):
    for idx, row in coopDF.iterrows():
        tracts2 = []
        coopPoly = row['geometry']
        for idx1, row2 in nriDF.iterrows():
            nriPoly = row2['geometry']    
            if nriPoly.intersects(coopPoly):
                tract = row2['TRACTFIPS']
                tracts2.append(tract)
        tractlist.append(tracts2)
           

# long lat values are the edges of the polygon
# df is the coop dataframe
# returns census tracts
def getCoopCensusTracts(coopDF):
    censusTracts1 = []
    censusTracts2 = []
    for i in coopDF['geometry']:
        censusTracts = []
        if (i.geom_type == 'Polygon'):
            for j in list(i.exterior.coords):
                long = j[0]
                lat = j[1]
                currTract = findCensusTract(lat, long)
                if currTract not in censusTracts:
                    censusTracts.append(currTract)
                if currTract not in censusTracts2:
                    censusTracts2.append(currTract)
        elif i.geom_type == 'MultiPolygon':
            coordList = [list(x.exterior.coords) for x in i.geoms]
            for i in coordList:
                long = j[0]
                lat = j[1]
                currTract = findCensusTract(lat, long)         
                if currTract not in censusTracts:
                    censusTracts.append(currTract)
                if currTract not in censusTracts2:
                    censusTracts2.append(currTract)
                    
        censusTracts1.append(censusTracts)
    #coopDF['censusTracts'] = censusTracts1
    return censusTracts2


# Retrieves Cooperative Data From Geo Json and saves to lists to be converted to DataFrame
# coopgeoJson -> cooperative geojson
# returns coop information and geometry
def getCoopData(coopgeoJson):
    data = []
    geom = []
    for i in coopgeoJson['features']:
        currData = (i['properties']['Member_Class'], i['properties']['Cooperative'], 
                    i['properties']['Data_Source'],i['properties']['Data_Year'],
                   i['properties']['Shape_Length'], i['properties']['Shape_Area'])
        if (i['geometry']['type'] == 'Polygon'):
            data.append(currData)
            geom.append(i['geometry']['coordinates'][0])
        elif (i['geometry']['type'] == 'MultiPolygon'):
            for j in i['geometry']['coordinates']:
                data.append(currData)
                geom.append(j[0])
    columns = ['Member_Class', 'Cooperative', 'Data_Source','Data_Year','Shape_Length', 'Shape_Area']
    return data, geom, columns

# Gets data for a list of coops
# coopgeoJson -> Coop data 
# listOfCoops -> list of cooperatives interested
def getCoopFromList(coopgeoJson, listOfCoops):
    coopData, coopGeo, columns = getCoopData(coopgeoJson)
    coopDF = createDF(coopData,  columns, coopGeo)
    geocoopDF = createGeoDF(coopDF[coopDF['Member_Class'] == 'Distribution'] )
    listOfCoopsDF = geocoopDF[geocoopDF['Cooperative'].isin(listOfCoops)]
    return listOfCoopsDF

# Relates census tract data to cooperative data
# coopDF -> cooperative datafrme
# geonriDF -> nri dataframe
def coopvcensusDF(coopDF, geonriDF):
    values = []
    geom = []
    columns = ['Cooperative_Name', 'BUILDVALUE','AGRIVALUE','EAL_VALT','EAL_VALB','EAL_VALP',
               'EAL_VALA','SOVI_SCORE','SOVI_RATNG','RESL_RATNG','RESL_VALUE','AVLN_AFREQ',
               'CFLD_AFREQ','CWAV_AFREQ','DRGT_AFREQ','ERQK_AFREQ','HAIL_AFREQ','HWAV_AFREQ',
               'HRCN_AFREQ','ISTM_AFREQ','LNDS_AFREQ','LTNG_AFREQ','RFLD_AFREQ','SWND_AFREQ',
               'TRND_AFREQ','TSUN_AFREQ','VLCN_AFREQ','WFIR_AFREQ','WNTW_AFREQ']

    for index, row in coopDF.iterrows():
        for j in row['censusTracts']:  
            # object information
            #Shape = geonriDF.loc[j]['Shape']
            if(j not in list(geonriDF.index)):
                continue

            BUILDVALUE = geonriDF.loc[j]['BUILDVALUE'] / geonriDF.loc[j]['Shape_Area'] #Building Value
            AGRIVALUE = geonriDF.loc[j]['AGRIVALUE']/ geonriDF.loc[j]['Shape_Area'] #Agriculture Value

            #Exp annual loss metrics
            EAL_VALT = geonriDF.loc[j]['EAL_VALT']/ geonriDF.loc[j]['Shape_Area'] # Expected Annual Loss - Total - Composite
            EAL_VALB = geonriDF.loc[j]['EAL_VALB'] / geonriDF.loc[j]['Shape_Area']# Expected Annual Loss - Building Value - Composite
            EAL_VALP = geonriDF.loc[j]['EAL_VALP']/ geonriDF.loc[j]['Shape_Area'] # Expected Annual Loss - Population - Composite
            EAL_VALA = geonriDF.loc[j]['EAL_VALA']/ geonriDF.loc[j]['Shape_Area'] # Expected Annual Loss - Agriculture Value - Composite

            # Social Vulnerabultiy
            SOVI_SCORE = geonriDF.loc[j]['SOVI_SCORE']/ geonriDF.loc[j]['Shape_Area'] # Social Vulnerability - Score
            SOVI_RATNG = geonriDF.loc[j]['SOVI_RATNG'] # Social Vulnerability - Rating


            # Community Resilience 
            RESL_RATNG = geonriDF.loc[j]['RESL_RATNG']# Community Resilience - Rating
            RESL_VALUE = geonriDF.loc[j]['RESL_VALUE']/ geonriDF.loc[j]['Shape_Area'] # Community Resilience - Value


            # Weather/ Natural Disaster Risk

            #Avalanche
            AVLN_AFREQ = geonriDF.loc[j]['AVLN_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Avalanche - Annualized Frequency

            # Coastal Flooding
            CFLD_AFREQ = geonriDF.loc[j]['CFLD_AFREQ'] / geonriDF.loc[j]['Shape_Area']# Coastal Flooding - Annualized Frequency

            # Cold Wave 
            CWAV_AFREQ= geonriDF.loc[j]['CWAV_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Cold Wave - Annualized Frequency

            #Drought
            DRGT_AFREQ=geonriDF.loc[j]['DRGT_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Drought - Annualized Frequency

            #EarthQuakes
            ERQK_AFREQ=geonriDF.loc[j]['ERQK_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Earthquake - Annualized Frequency

            #Hail
            HAIL_AFREQ=geonriDF.loc[j]['HAIL_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Hail - Annualized Frequency

            #Heat Wave
            HWAV_AFREQ=geonriDF.loc[j]['HWAV_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Heat Wave - Annualized Frequency

            #Hurricane
            HRCN_AFREQ= geonriDF.loc[j]['HRCN_AFREQ'] / geonriDF.loc[j]['Shape_Area']# Hurricane - Annualized Frequency

            # Ice Storm
            ISTM_AFREQ= geonriDF.loc[j]['ISTM_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Ice Storm - Annualized Frequency

            #LandSlide
            LNDS_AFREQ= geonriDF.loc[j]['LNDS_AFREQ'] / geonriDF.loc[j]['Shape_Area']# Landslide - Annualized Frequency

            #Lightning
            LTNG_AFREQ=geonriDF.loc[j]['LNDS_EVNTS'] / geonriDF.loc[j]['Shape_Area']# Lightning - Annualized Frequency

            #Riverline Flooding
            RFLD_AFREQ = geonriDF.loc[j]['RFLD_AFREQ'] / geonriDF.loc[j]['Shape_Area']# Riverine Flooding - Annualized Frequency

            #Strong Wind
            SWND_AFREQ= geonriDF.loc[j]['SWND_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Strong Wind - Annualized Frequency

            #Tornado
            TRND_AFREQ=geonriDF.loc[j]['TRND_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Tornado - Annualized Frequency

            #Tsunami
            TSUN_AFREQ= geonriDF.loc[j]['TSUN_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Tsunami - Annualized Frequency

            #Volcanic Activity
            VLCN_AFREQ= geonriDF.loc[j]['VLCN_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Volcanic Activity - Annualized Frequency

            #Wildfire
            WFIR_AFREQ= geonriDF.loc[j]['WFIR_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Wildfire - Annualized Frequency

            #Winter Weather
            WNTW_AFREQ= geonriDF.loc[j]['WNTW_AFREQ']/ geonriDF.loc[j]['Shape_Area'] # Winter Weather - Annualized Frequency


            rowVals = [row['Cooperative'],BUILDVALUE,AGRIVALUE,EAL_VALT,EAL_VALB,EAL_VALP,
               EAL_VALA,SOVI_SCORE,SOVI_RATNG,RESL_RATNG,RESL_VALUE,AVLN_AFREQ,
               CFLD_AFREQ,CWAV_AFREQ,DRGT_AFREQ,ERQK_AFREQ,HAIL_AFREQ,HWAV_AFREQ,
               HRCN_AFREQ,ISTM_AFREQ,LNDS_AFREQ,LTNG_AFREQ,RFLD_AFREQ,SWND_AFREQ,
               TRND_AFREQ,TSUN_AFREQ,VLCN_AFREQ,WFIR_AFREQ,WNTW_AFREQ]

            values.append(rowVals)
            geom.append(row['geometry'])
            finalDF = createDF(values, columns, geom)
            
            return finalDF.set_index('Cooperative_Name')
        
# Correlative Testing
# run correlation tests
# return corr, corr2 -> correlation matrix and correlation matrix >.7
def run_correlationTesting(listOfCoops, stateName, nrigeoJson, coopGeoJson):
    coopData, coopGeo, columns = getCoopData(coopGeoJson)
    coopDF = createDF(coopData,  columns, coopGeo)
    geocoopDF = createGeoDF(coopDF[coopDF['Member_Class'] == 'Distribution'] )
    coopListGeocoopDF = geocoopDF[geocoopDF['Cooperative'].isin(listOfCoops)]
                                  
    geom, data, headers = getTractDatabyState(nrigeoJson, stateName)
    geomLA = runTransformation(geom)
    laDF = createDF(data, headers, geomLA)
    nriStateDF = createGeoDF(laDF)
                                  
    tractList = getCoopCensusTracts(coopListGeocoopDF)
                                  
    findallTracts(nriStateDF,geocoopDF, tractList)
    
    coopListGeocoopDF['censusTracts'] = tractList
                                  
                                  
                                  
    combDF = coopvcensusDF(coopListGeocoopDF,nriStateDF)
                                  
    corr = combDF.corr(method='pearson')                           
    mask = np.abs(corr) < .7
    corr2 = corr[~mask]
                                  
                                  
    return corr, corr2      
                                 
def work(modelDir, inputDict):
    ''' Run the model in its directory. '''
    outData = {}
    omd_file_path = pJoin(omf.omfDir,'static','publicFeeders', inputDict['inputDataFileName'])
    #geo.map_omd(inputDict['InputFilePath'], modelDir, open_browser=False )
    geo.map_omd(omd_file_path, modelDir, open_browser=False)
    outData['resilienceMap'] = open( pJoin( modelDir, "geoJson_offline.html"), 'r' ).read()
    #geojson = pJoin(omf.omfDir,'static','publicFeeders', omdfileName)
    outData['soviData'] = json.dumps('/Users/davidarmah/Documents/Python/Testing /out.geojson')

  


    return outData
   


#def test():
 #   createLegend()
     #omd_file_path = pJoin(omf.omfDir,'static','publicFeeders')
     #print(omd_file_path)
     
def new(modelDir):
    omdfileName = 'greensboro_NC_rural'
    omd_file_path = pJoin(omf.omfDir,'static','publicFeeders', omdfileName) 
    #omdFile = '/Users/davidarmah/Documents/OMF/omf/omf/static/publicFeeders/greensboro_NC_rural.omd'

    #with open(f'{modelDir}/omdfileName + '.omd', 'r') as omdFile:
       #  omd = json.load(omdFile)

    with open(omd_file_path + '.omd') as inFile:
        fullFile = json.load(inFile)

    defaultInputs = {
		"modelType": modelName,
		"inputDataFileName": omdfileName + '.omd',
        "feederName": omdfileName,
        "inputDataFileContent": 'omd',
        "optionalCircuitFile" : 'on',
		"created":str(datetime.datetime.now())
	}




    return __neoMetaModel__.new(modelDir, defaultInputs)

@neoMetaModel_test_setup
def tests():
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
	#_disabled_tests()
	#test()
