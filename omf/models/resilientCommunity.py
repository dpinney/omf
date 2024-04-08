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
#import shapefile
import io
from io import BytesIO
import numpy as np
import json
import math
import pandas as pd
#from shapely.geometry import Polygon
#from shapely.geometry import Point
#from pyproj import Transformer
#import geopandas as gpd
#import matplotlib.colorbar as colorbar
#import matplotlib.colors as clr
#import matplotlib.pyplot as plt
#import base64
import networkx as nx


# OMF imports
from omf import feeder, geo
from omf.models.voltageDrop import drawPlot
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

from omf.solvers.opendss import *
from omf.comms import *
from omf.solvers.opendss.dssConvert import *



# GEO py imports



# Model metadata:
modelName, template = __neoMetaModel__.metadata(__file__)
hidden = True

  

def retrieveCensusNRI():
    '''
    Retrieves necessary data from ZIP File and exports to geojson
    Input: dataURL -> URL to retrieve data from
    returns geojson of census NRI data
    '''
    
    try:
        #headers
        hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko)  Chrome/23.0.1271.64 Safari/537.11','Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3','Accept-Encoding': 'none','Accept-Language': 'en-US,en;q=0.8','Connection': 'keep-alive'}
        #FEMA nri data url
        nridataURL = "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload//NRI_Shapefile_CensusTracts/NRI_Shapefile_CensusTracts.zip"
        r = requests.get(nridataURL, headers=hdr)
        z = zipfile.ZipFile(BytesIO(r.content))
		# get file names needed to build geoJSON
        shpPath = [x for x in z.namelist() if x.endswith('.shp')][0]
        dbfPath = [x for x in z.namelist() if x.endswith('.dbf')][0]
        prjPath = [x for x in z.namelist() if x.endswith('.prj')][0]
        # create geojson from datafiles
        with shapefile.Reader(shp=BytesIO(z.read(shpPath)), dbf=BytesIO(z.read(dbfPath)), prj=BytesIO(z.read(prjPath))) as shp:
            geojson_data = shp.__geo_interface__
            prefix = list(pathlib.Path(__file__).parts)
            prefix[7] = 'static'
            prefix[8] = 'testFiles'
            outfile = pathlib.Path(*prefix) / 'census_and_NRI_database_MAR2023.json'
            with open(outfile, 'w') as f:
                json.dump(geojson_data, f,indent=4)
                return outfile
    except Exception as e:
        print("Error trying to retrieve FEMA NRI Census Data in GeoJson format")
        print(e)


def findCensusTract(lat, lon):
    '''
    Finds Census Tract at a given lon / lat incorporates US Census Geolocator API
    Input: lat -> specified latitude value
    Input: lon -> specified longitude value
    return censusTract ->  census Tract found at location
    '''
    try:
        # Requested for API Key to bypass api load limits
        request_url = "https://geo.fcc.gov/api/census/block/find?latitude="+str(lat)+"&longitude="+str(lon)+ "&censusYear=2020&format=json&key=bc86c8cfc930e7c10b81d6683c6a316f5fcb857b"
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        resp = opener.open(request_url, timeout=50)
        censusJson = json.loads(resp.read())
        censusTract = censusJson['Block']['FIPS'][:-4]
        return  censusTract
    except Exception as e:
        print("Error trying to retrieve tract information from Census API")
        print(e)



def getCensusNRIData(nrigeoJson, tractList):
    '''
    Get Census Tract Social Vulnerability Data
    Input: nrigeoJson -> nri geoJson data
    Input: tractList -> list of tracts
    return geomData, soviData, headers -> list of geometrys, social vulnerability for tracts found in list, column names associated with data cols.
    '''
    nriData = []
    geomData = []
    headers = list(nrigeoJson['features'][0]['properties'].keys())
    for i in nrigeoJson['features']:
        tractID = i['properties']['TRACTFIPS']
        if tractID in tractList:
            properties = []
            for i in i['properties']:
                properties.append(i)
            geom = i['geometry']['coordinates'][0]
            geomData.append(geom)
            nriData.append(properties)

    return geomData, nriData, headers


def getTractDatabyState(nrigeoJson,stateName):
    '''
    Gets Census Tract data from a specified state
    input: nrigeoJson -> nri geojson
    input stateName -> Specified state name
    '''
    data = []
    geom = []
    headers = list(nrigeoJson['features'][0]['properties'].keys())
    for i in nrigeoJson['features']:
        state = i['properties']['STATE']
        if state == stateName:
            properties = []
            for k in i['properties']:
                properties.append(i['properties'][k])
            if (i['geometry']['type'] == 'MultiPolygon'):
                for j in i['geometry']['coordinates']:
                    geom.append(j)
                    data.append(properties)
            else:
                geom.append(i['geometry']['coordinates'][0])
                data.append(properties)
    return geom, data, headers


def getCircuitNRI(pathToOmd):
    '''
    find census located at specified circuit nodes
    Input:pathToOmd -> path to circuit file
    return censusTracts -> census tract
    '''
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


def transform(coordList):
    '''
    transform coordinates from WGS_1984_Web_Mercator_Auxiliary_Sphere(EPSG 3857) to EPSG:4326
    Input: coordList -> list of coordinates (geometry)
    return coordList -> transformed coordinates
    '''
    for idx, i in enumerate(coordList):
        lat,lon = i[0], i[1]
        x = (lat * 180) / 20037508.34
        y = (lon * 180) / 20037508.34
        y = (math.atan(math.pow(math.e, y * (math.pi / 180))) * 360) / math.pi - 90
        coordList[idx] = [x,y]
        
    return coordList


def runTransformation(geos):
    '''
    runs transformations for a list of geometries
    Input: geos -> list of geometry
    return geoTransformed -> transofrmed list of geometries
    '''
    geoTransformed = []
    for i in geos:
        if (isinstance(i[0][0], float)):
            geoTransformed.append(transform(i))
        else:
            geoTransformed.append(transform(i[0]))
    return geoTransformed


def createDF(tractData, columns, geoTransformed):
    '''
    Creates Pandas DF from list of data containing GeoData 
    input: tractData -> Data associated with data
    input: columns -> columns for data
    input: geoTransformed -> EPSG:4326 transformed geometry
    '''
    data = pd.DataFrame(tractData, columns = columns)
    data['geometry'] = geoTransformed
    return data


def createGeoDF(df):
    '''
    Creates GeoPandas DF From pandas DF
    input: df -> pandas df
    return geo -> geodataframe
    '''
    df['geometry'] = df['geometry'].apply(Polygon)
    geo = gpd.GeoDataFrame(df, geometry=df["geometry"], crs="EPSG:4326")
    return geo


def createLegend():
    '''
    creates legend for social vulnerability pologons to overlay with map_omd map
    '''
    colors = ["blue", "lightblue", "lightgreen", "yellow", "gray", "black"]
    labels = ['Very High', 'Rel. High', 'Rel. Moderate', 'Rel. Low', 'Very Low', "Data Unavailable"]
    num_colors = len(colors)
    cmap_ = clr.ListedColormap(colors)
    fig = plt.figure()
    ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
    cb = colorbar.ColorbarBase(ax, orientation='horizontal',cmap=cmap_, norm=plt.Normalize(-.3, num_colors - .5))
    plt.title("Social Vulnerability Legend")
    cb.set_ticks(range(num_colors))
    cb.ax.set_xticklabels(labels)
    path = pJoin(omf.omfDir,'static','testFiles','resilientCommunity', 'legend.png')

    plt.savefig(path,bbox_inches='tight')

    return path



def findallTracts(nriDF, coopDF, tractlist):
    '''
    nriDF -> nri dataframe
    coopDF -> cooperative Dataframe
    tractList -> list of tracts corresponding to the outer borders of cooperative
    '''
    for idx, row in coopDF.iterrows():
        tracts2 = []
        coopPoly = row['geometry']
        for idx1, row2 in nriDF.iterrows():
            nriPoly = row2['geometry']
            if nriPoly.intersects(coopPoly):
                tract = row2['TRACTFIPS']
                tracts2.append(tract)
        tractlist.append(tracts2)


def getCoopCensusTracts(coopDF):
    '''
    long lat values are the edges of the polygon
    coopdf is the cooperative dataframe
    returns list of census tracts
    '''
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



def getCoopData(coopgeoJson):
    '''
    Retrieves Cooperative Data From Geo Json and saves to lists to be converted to DataFrame
    coopgeoJson -> cooperative geojson
    returns list of cooperative data, geometry, and column names for the cooperative data
    '''
    data = []
    geom = []
    for i in coopgeoJson['features']:
        currData = (i['properties']['Member_Class'], i['properties']['Cooperative'], i['properties']['Data_Source'],i['properties']['Data_Year'],i['properties']['Shape_Length'], i['properties']['Shape_Area'])

        if (i['geometry']['type'] == 'Polygon'):
            data.append(currData)
            geom.append(i['geometry']['coordinates'][0])
        elif (i['geometry']['type'] == 'MultiPolygon'):
            for j in i['geometry']['coordinates']:
                data.append(currData)
                geom.append(j[0])
    columns = ['Member_Class', 'Cooperative', 'Data_Source','Data_Year','Shape_Length', 'Shape_Area']
    return data, geom, columns


def getCoopFromList(coopgeoJson, listOfCoops):
    '''
    Gets data for a list of coops
    coopgeoJson -> Coop data
    listOfCoops -> list of cooperatives interested 
    
    '''
    coopData, coopGeo, columns = getCoopData(coopgeoJson)
    coopDF = createDF(coopData,  columns, coopGeo)
    geocoopDF = createGeoDF(coopDF[coopDF['Member_Class'] == 'Distribution'] )
    listOfCoopsDF = geocoopDF[geocoopDF['Cooperative'].isin(listOfCoops)]
    return listOfCoopsDF


def coopvcensusDF(coopDF, geonriDF):
    '''
    Relates census tract data to cooperative data
    coopDF -> cooperative datafrme
    geonriDF -> nri dataframe
    returns dataframe containing relevant columns and 
    '''
    values = []
    geom = []
    columns = ['Cooperative_Name', 'BUILDVALUE','AGRIVALUE','EAL_VALT','EAL_VALB','EAL_VALP','EAL_VALA','SOVI_SCORE','SOVI_RATNG','RESL_RATNG','RESL_VALUE','AVLN_AFREQ','CFLD_AFREQ','CWAV_AFREQ','DRGT_AFREQ','ERQK_AFREQ','HAIL_AFREQ','HWAV_AFREQ','HRCN_AFREQ','ISTM_AFREQ','LNDS_AFREQ','LTNG_AFREQ','RFLD_AFREQ','SWND_AFREQ','TRND_AFREQ','TSUN_AFREQ','VLCN_AFREQ','WFIR_AFREQ','WNTW_AFREQ']

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


            rowVals = [row['Cooperative'],BUILDVALUE,AGRIVALUE,EAL_VALT,EAL_VALB,EAL_VALP,EAL_VALA,SOVI_SCORE,SOVI_RATNG,RESL_RATNG,RESL_VALUE,AVLN_AFREQ,CFLD_AFREQ,CWAV_AFREQ,DRGT_AFREQ,ERQK_AFREQ,HAIL_AFREQ,HWAV_AFREQ,HRCN_AFREQ,ISTM_AFREQ,LNDS_AFREQ,LTNG_AFREQ,RFLD_AFREQ,SWND_AFREQ,TRND_AFREQ,TSUN_AFREQ,VLCN_AFREQ,WFIR_AFREQ,WNTW_AFREQ]

            values.append(rowVals)
            geom.append(row['geometry'])
            finalDF = createDF(values, columns, geom)
            
            return finalDF.set_index('Cooperative_Name')
        

def run_correlationTesting(listOfCoops, stateName, nrigeoJson, coopGeoJson):
    '''
    Correlative Testing
    run correlation tests
    listOfCoops -> list of cooperatives
    stateName -> Name of state being looked at
    nrigeoJson -> dict of nri data
    coopGeoJson -> dict of cooperative data
    return corr, corr2 -> correlation matrix and correlation matrix >.7
    '''
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


def getDownLineLoads(pathToOmd,nriGeoJson):
    '''
    Retrieves downline loads for a circuit and retrieves nri data for each of the loads within the circuit
    pathToOmd -> path to the omdfile
    nriGeoJson -> dict of nri data
    return obDict, loadDict -> list of objects, dict of loads for given omd file
    '''
    omd = json.load(open(pathToOmd))
    obDict = {}
    loads = {}
    tracts = {}
    tractData = []
    geos = []

    #loadServedVals = []
    for ob in omd.get('tree', {}).values():
        obType = ob['object']
        obName = ob['name']
        key = obType + '.' + obName
        obDict[key] = ob
        # save load information
        
        if (obType == 'load'):
            loads[obName] = {
                        'base crit score':None}#None,'percentile':None}
            kw = float(ob['kw'])
            kvar = float(ob['kvar'])
            kv = float(ob['kv'])
            # For each load, estimate the number of persons served. 
            #Use the following equation sqrt(kw^2 + kvar^2)/5 kva = # of homes served by that load
            # assume household is 4
            loads[obName]['base crit score']= ((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5)) * 4

            lat = float(ob['latitude'])
            long = float(ob['longitude'])

            tract = findCensusTract(lat, long)

            ## CHECKS IF WE HAVE ALREADY LOOKED FOR THE TRACT IN QUESTION

            
            while tract == None:
                tract = findCensusTract(lat, long)

            if tract in tracts:
                svi_score = float(tracts.get(tract)['SOVI_SCORE'])
                sovi_rtng = tracts.get(tract)['SOVI_RATNG']
                loads[key]['SOVI_SCORE'] = svi_score
                loads[key]['SOVI_RATNG'] = sovi_rtng
                loads[key]['cen_tract'] = tract
                loads[key]['community crit score'] = (((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5)) * 4) *  svi_score
            
            else:
                for i in nriGeoJson['features']:
                    tractID = i['properties']['TRACTFIPS']

                    if tractID == tract:
                        svi_score = float(i['properties']['SOVI_SCORE'])
                        sovi_rtng = i['properties']['SOVI_RATNG']
                        #loads[key]['sovitract'] = svi_score
                        loads[key]['SOVI_SCORE'] = svi_score
                        loads[key]['SOVI_RATNG'] = sovi_rtng
                        loads[key]['cen_tract'] = tract


                        
                        
                        if (i['geometry']['type'] == 'MultiPolygon'):
                            for j in i['geometry']['coordinates']:
                                geos.append(j)
                                tractData.append((tract, svi_score, sovi_rtng))
                        else:
                            geos.append(i['geometry']['coordinates'][0])
                            tractData.append((tract, svi_score, sovi_rtng))


                        loads[key]['community crit score'] = (((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5)) * 4) *  svi_score

                        tracts[tractID] = i['properties']
                        break

            
    getPercentile(loads, 'base crit score')
    getPercentile(loads, 'community crit score')
    transformedGeos = runTransformation(geos)

    df = createDF(tractData, ['census_tract', "SOVI_SCORE", "SOVI_RATNG"], transformedGeos)
    geoDF = createGeoDF(df)
    
    #geoDF.to_file('/Users/davidarmah/Documents/omf/omf/static/testFiles/resilientCommunity/geoShapes.geojson', driver="GeoJSON")
            


    #loadServedVals.append((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5))
                
            

    

    


    
    del omd

    digraph = createGraph(pathToOmd)
    nodes = digraph.nodes()

    namesToKeys = {v.get('name'):k for k,v in obDict.items()}
    
    
    for obKey, ob in obDict.items():
        obType = ob['object']

        obName = ob['name']

        obTo = ob.get('to')

        if obName in nodes:

            startingPoint = obName

        elif obTo in nodes:

            startingPoint = obTo

        else:

            continue

        successors = nx.dfs_successors(digraph, startingPoint).values()

        ob['downlineObs'] = []

        ob['downlineLoads'] = []

        for listofVals in successors:

            for element in listofVals:

                elementKey = namesToKeys.get(element)

                elementType = elementKey.split('.')[0]



                if elementKey not in ob['downlineObs']:

                    ob['downlineObs'].append(elementKey)

                if elementKey not in ob['downlineLoads'] and elementType == 'load':

                    ob['downlineLoads'].append(elementKey)
    

    #BaseCriticallityWeightedAvg(obDict, loads)
    return obDict, loads, geoDF


def getPercentile(loads, columnName):
    '''
    Gets percentile of specified column
    loads -> dict of loads
    columnName -> specified column name
    '''

    loadServedVals = [v.get(columnName) for k,v in loads.items()]

    # calculate percentile for each load
    pairs = list(zip(loadServedVals, range(len(loadServedVals))))

    pairs.sort(key=lambda p: p[0])
    result = [0 for i in range(len(loadServedVals))]
    for rank in range(len(loadServedVals)):
        original_index = pairs[rank][1]
        result[original_index] = rank * 100.0 / (len(loadServedVals)-1)
    if (columnName == "base crit score"):
        new_str = 'base crit index'
    else:
        new_str = 'community crit index'
    for i, (k,v) in enumerate(loads.items()):
        loads[k][new_str] = round(result[i],2)

def getDownLineLoadsEquipment(pathToOmd,nriGeoJson, equipmentList):

    '''
    Retrieves downline loads for specific set of equipment and retrieve nri data for each of the equipment
    pathToOmd -> path to the omdfile
    nriGeoJson -> dict of nri data
    equipmentList -> list of equipment of interest
    '''
    omd = json.load(open(pathToOmd))
    obDict = {}
    loads = {}
    tracts = {}
    tractData = []
    geos = []
    cols = ['TRACT','BUILDVALUE','AGRIVALUE','EAL_VALT','EAL_VALB','EAL_VALP','EAL_VALA','SOVI_SCORE','SOVI_RATNG','RESL_RATNG','RESL_VALUE','AVLN_AFREQ','CFLD_AFREQ','CWAV_AFREQ','DRGT_AFREQ','ERQK_AFREQ','HAIL_AFREQ','HWAV_AFREQ','HRCN_AFREQ','ISTM_AFREQ','LNDS_AFREQ','LTNG_AFREQ','RFLD_AFREQ','SWND_AFREQ','TRND_AFREQ','TSUN_AFREQ','VLCN_AFREQ','WFIR_AFREQ','WNTW_AFREQ']
    for ob in omd.get('tree', {}).values():
        obType = ob['object']
        obName = ob['name']
        key = obType + '.' + obName
        obDict[key] = ob
        # save load information
        
        if (obType == 'load'):
            loads[key] = {
                        "base crit score":None}#None,'percentile':None}
            kw = float(ob['kw'])
            kvar = float(ob['kvar'])
            kv = float(ob['kv'])
            # For each load, estimate the number of persons served.
            #Use the following equation sqrt(kw^2 + kvar^2)/5 kva = # of homes served by that load
            # assume household is 4
            loads[key]["base crit score"]= ((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5)) * 4


            
            lat = float(ob['latitude'])
            long = float(ob['longitude'])
            
            tract = findCensusTract(lat, long)

            ## CHECKS IF WE HAVE ALREADY LOOKED FOR THE TRACT IN QUESTION

            if tract in tracts:
                svi_score = round(float(tracts.get(tract)['SOVI_SCORE']),2)
                #loads[key] = tracts.get(tract)
                loads[key]["community crit score"] = round((((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5)) * 4) *  svi_score,2)
                loads[key]['SOVI_SCORE'] = svi_score
            else:
                for i in nriGeoJson['features']:
                    tractID = i['properties']['TRACTFIPS']

                    if tractID == tract:
                        # TO DO: add all values in census nri to the loads vals
                        vals= []
                        for col in cols:
                            vals.append(i['properties'][col])
                        

                        #vals = list(i['properties'].values())

                        svi_score = round(float(i['properties']['SOVI_SCORE']),2)
                        #sovi_rtng = i['properties']['SOVI_RATNG']
                        #loads[key]['sovitract'] = svi_score
                        loads[key]['SOVI_SCORE'] = svi_score
                        #loads[key]['SOVI_RATNG'] = sovi_rtng
                        #loads[key]['cen_tract'] = tract
                        #loads[key]['SOVI_SCORE'] = svi_score
                        loads[key]["community crit score"] = round((((math.sqrt((kw * kw) + (kvar * kvar) ))/ (5)) * 4) *  svi_score,2)

                        tracts[tractID] = i['properties']

                        if (i['geometry']['type'] == 'MultiPolygon'):
                            for j in i['geometry']['coordinates']:
                                geos.append(j)
                                tractData.append(vals)
                        else:
                            geos.append(i['geometry']['coordinates'][0])
                            tractData.append(vals)

                        break

            

            
    getPercentile(loads, "base crit score")
    getPercentile(loads, 'community crit score')
    transformedGeos = runTransformation(geos)

    #columns = list(nriGeoJson['features'][0]['properties'].keys())
    df = createDF(tractData, cols, transformedGeos)
    geoDF = createGeoDF(df)
    
    #geoDF.to_file('/Users/davidarmah/Documents/omf/omf/static/testFiles/resilientCommunity/geoShapes.geojson', driver="GeoJSON")
            
        
    del omd

    digraph = createGraph(pathToOmd)
    nodes = digraph.nodes()

    namesToKeys = {v.get('name'):k for k,v in obDict.items()}
    
    
    for obKey, ob in obDict.items():
        obType = ob['object']

        obName = ob['name']

        obTo = ob.get('to')

        if obName in nodes:

            startingPoint = obName

        elif obTo in nodes:

            startingPoint = obTo

        else:

            continue

        successors = nx.dfs_successors(digraph, startingPoint).values()

        ob['downlineObs'] = []

        ob['downlineLoads'] = []

        if obType in equipmentList:

            for listofVals in successors:

                for element in listofVals:

                    elementKey = namesToKeys.get(element)

                    elementType = elementKey.split('.')[0]

                    if elementKey not in ob['downlineObs']:

                        ob['downlineObs'].append(elementKey)

                    if elementKey not in ob['downlineLoads'] and elementType == 'load':

                        ob['downlineLoads'].append(elementKey)


    filteredObDict = {k:v  for k,v in obDict.items() if v.get('object') in equipmentList}



    # perform weighted avg base criticality for equipment

    newObsDict = BaseCriticallityWeightedAvg(filteredObDict, loads)



    # perform weighted avg community criticality for equipment

    getPercentile(newObsDict, 'base crit score')
    getPercentile(newObsDict, 'community crit score')


    return newObsDict,loads, geoDF

def BaseCriticallityWeightedAvg(obsDict, loadsDict):
    '''
    Calculates base criticality for pieces of equipment that are not loads. Performs weighted average
    obsDict -> dict of all circuit objects
    loadsDict -> dict of loads
    return newDict -> dict of objects weighted avg criticality values
    '''
    newDict = {}
    for k,v in obsDict.items():
        weights=0
        sum=0
        sum2 = 0

        
        if(len(v['downlineLoads']) > 0):
            count = len(v['downlineLoads'])
            for j in v['downlineLoads']:
                ob = loadsDict.get(j)
                weights+=ob['SOVI_SCORE']
                comm_crit_sum+=ob['community crit score'] * ob['SOVI_SCORE']
                base_crit_sum+=ob['base crit score']
            obsDict[k]['base crit score'] = round(base_crit_sum,2)
            obsDict[k]['community crit score'] = round(comm_crit_sum/weights,2)
        else:
            obsDict[k]['base crit score'] = 0
            obsDict[k]['community crit score'] = 0

    getPercentile(obsDict, 'community crit score')
    getPercentile(obsDict, 'base crit score')

    return obsDict
    



def addLoadInfoToOmd(loadsDict, omdDict):
    '''
    adds criticality values to omd file for all objects
    loadsDict -> dict of loads
    omdDict -> dict of omd objects
    returns new dict of omd objects
    '''
    for ob in omdDict.get('tree', {}).values():
        if ob['object'] == 'load':
            obType = ob['object']
            obName = ob['name']
            k = obType + '.' + obName

            bcs_score = loadsDict[k]['base crit score']
            ccs_score = loadsDict[k]['community crit score']
            bcs_index = loadsDict[k]['base crit score']
            ccs_index = loadsDict[k]['community crit index']
            ob['base crit score'] = bcs_score
            ob['community crit score'] = ccs_score
            ob['community crit index'] = ccs_index
            ob['base crit index'] = bcs_index
        else:
            continue
    return omdDict


def addEquipmentInfoToOmd(obDict, omdDict, equipList):
    '''
    adds criticality values to omd file for all objects
    loadsDict -> dict of loads
    omdDict -> dict of omd objects
    returns new dict of omd objects
    '''
    for ob in omdDict.get('tree', {}).values():
        obType = ob['object']
        obName = ob['name']
        k = obType + '.' + obName

        bcs_score = obDict[k]['base crit score']
        ccs_score = obDict[k]['community crit score']
        bcs_index = obDict[k]['base crit score']
        ccs_index = obDict[k]['community crit index']
        ob['base crit score'] = bcs_score
        ob['community crit score'] = ccs_score
        ob['community crit index'] = ccs_index
        ob['base crit index'] = bcs_index
    return omdDict


def createColorCSV(modelDir, loadsDict):
    '''
    Creates colorby CSV to color loads within the circuit
    modelDir -> model directory
    loadsDict -> dict of loads
    '''
    new = {k.split('load.')[1]:v for k,v in loadsDict.items()}
    new_df = pd.DataFrame.from_dict(new, orient='index')
    new_df.to_csv(Path(modelDir, 'color_by.csv'), index=True)


def work(modelDir, inputDict):
    ''' Run the model in its directory. '''
    outData = {}

    # files
    omd_file_path = pJoin(omf.omfDir,'static','testFiles','resilientCommunity', inputDict['inputDataFileName'])
    #census_nri_path = pJoin(omf.omfDir,'static','testFiles','census_and_NRI_database_MAR2023.json')
    census_nri_path = '/Users/davidarmah/Documents/Python Code/PCCEC/CensusNRI.json'
    loads_file_path = pJoin(omf.omfDir,'static','testFiles','resilientCommunity', 'loads2.json')
    obs_file_path = pJoin(omf.omfDir,'static','testFiles','resilientCommunity', 'objects3.json')
    geoJson_shapes_file = pJoin(omf.omfDir,'static','testFiles','resilientCommunity', 'geoshapes.geojson')
    
    # check if we want to refresh the nri data
    #import sys as sys
    # sys.stdout.write(inputDict)
    if not os.path.exists(census_nri_path):
        retrieveCensusNRI()
    elif inputDict['refresh'] == True:
        retrieveCensusNRI()
        createLegend()
    
    
    # check what equipment we want to look for

    equipmentList = []

    if (inputDict['lines'].lower() == 'yes' ):
        equipmentList.append('line')
    if (inputDict['transformers'].lower() == 'yes' ):
        equipmentList.append('transformer')
    if (inputDict['fuses'].lower() == 'yes' ):
        equipmentList.append('fuse')
    if (inputDict['buses'].lower() == 'yes' ):
        equipmentList.append('bus')
    

    #load census data

    with open(census_nri_path) as file:
        nricensusJson = json.load(file)

    
    # check downline loads
    obDict, loads, geoDF = getDownLineLoadsEquipment(omd_file_path, nricensusJson, equipmentList)

    # color vals based on selected column
    
    createColorCSV(modelDir, loads)
    

    if(inputDict['loadCol'] == 'Base Criticality Score'):
        colVal = "1"
    elif (inputDict['loadCol'] == 'Community Criticality Score'):
        colVal = "5"
    elif(inputDict['loadCol'] == 'Base Criticality Index'):
        colVal = "6"
    elif(inputDict['loadCol'] == 'Community Criticality Index'):
        colVal = "7"
    else:
        colVal = None
    
    # Load Geojson file more efficiently

    geoDF.to_file(geoJson_shapes_file, driver="GeoJSON")
    with open(geoJson_shapes_file) as f1:
        geoshapes =  json.load(f1)
    attachment_keys = {
	"coloringFiles": {
		"color_by.csv": {
			"csv": "<content>",
			"colorOnLoadColumnIndex": colVal
		}
	}
    ,
    "geojsonFiles":{
        "geoshapes.geojson": {
            "json": json.dumps(geoshapes)
        }

    }
    }


    with open(omd_file_path) as file1:
        init_omdJson = json.load(file1)
    

    newOmdJson = addLoadInfoToOmd(loads, init_omdJson)

    omdJson = addEquipmentInfoToOmd(obDict, newOmdJson)





    #omdJson = addToOmd1(newDict, init_omdJson, equipmentList)
    data = Path(modelDir, 'color_by.csv').read_text()

    # TO DO

    attachment_keys['coloringFiles']['color_by.csv']['csv'] = data
    
    omd = json.load(open(omd_file_path))
    
    new_path = Path(modelDir, 'color_test.omd')
	
    omdJson['attachments'] = attachment_keys

    with open(new_path, 'w+') as out_file:
        json.dump(omdJson, out_file, indent=4)



    #outData['nri_data'] = json.dumps(nricensusJson)

    geo.map_omd(new_path, modelDir, open_browser=False)
    
    outData['resilienceMap'] = open( pJoin( modelDir, "geoJson_offline.html"), 'r' ).read()
    outData['geojsonData'] = open(geoJson_shapes_file, 'r').read()


    
    headers1 = ['Load Name', 'Base Criticality Score', 'Base Criticality Index']
    load_names = list(loads.keys())
    base_criticality_score_vals1 = [value.get('base crit score') for key, value in loads.items()]
    base_criticity_index_vals1 = [value.get('base crit index') for key, value in loads.items()]


    outData['loadTableHeadings'] = headers1
    outData['loadTableValues'] = list(zip(load_names, base_criticality_score_vals1, base_criticity_index_vals1))


    headers2 = ['Object Name', 'Base Criticality Score', 'Base Criticallity Index', 'Community Criticality Score', 'Community Criticality Index']
    object_names = list(obDict.keys())
    base_criticality_score_vals2 = [value.get('base crit score') for key, value in obDict.items()]
    base_criticity_index_vals2 = [value.get('base crit index') for key, value in obDict.items()]
    community_criticality_score_vals2 = [value.get('community crit score') for key, value in obDict.items()]
    community_criticity_index_vals = [value.get('community crit index') for key, value in obDict.items()]


    outData['loadTableHeadings2'] = headers2
    outData['loadTableValues2'] = list(zip(object_names, base_criticality_score_vals2, base_criticity_index_vals2,community_criticality_score_vals2,community_criticity_index_vals ))

    str1 = '''
    loads_file_path = pJoin(omf.omfDir,'static','testFiles', 'resilientCommunity', 'loads2.json')
    geo.map_omd(omd_file_path, modelDir, open_browser=False )
    #geo.map_omd(omd_file_path, modelDir, open_browser=False)
    outData['resilienceMap'] = open( pJoin( modelDir, "geoJson_offline.html"), 'r' ).read()
    #outData['geoshapes'] = open(geoshapes_geoPath, 'r').read()

    fullFile = json.load(open(loads_file_path))

    headers = ['Load Name', 'People Served', 'Base Criticallity']
    load_names = list(fullFile.keys())
    people_served_vals = [value.get('base_criticality_score') for key, value in fullFile.items()]
    percentile_vals = [value.get('base_criticality_score_index') for key, value in fullFile.items()]


    outData['loadTableHeadings'] = headers
    outData['loadTableValues'] = list(zip(load_names, people_served_vals, percentile_vals))
    

    '''


    return outData


def test():
    #omdPath = '/Users/davidarmah/Downloads/cleandssout.omd'
    #dssPath = '/Users/davidarmah/Downloads/flat_Master_clean.DSS'
    mergedOmdPath = '/Users/davidarmah/Documents/omf/omf/static/testFiles/resilientCommunity/mergedGreensboro.omd'
    loads = '/Users/davidarmah/Documents/omf/omf/static/testFiles/resilientCommunity/loads2.json'
    nrijsonPath = '/Users/davidarmah/Documents/Python Code/PCCEC/CensusNRI.json'
    #equipmentPath = '/Users/davidarmah/Documents/omf/omf/static/testFiles/resilientCommunity/equipmentDict.csv'
    #newomdPath = '/Users/davidarmah/Documents/omf/omf/static/publicFeeders/iowa240_in_Florida.omd'
    #newomdPath = '/Users/davidarmah/Documents/omf/omf/static/publicFeeders/iowa240_in_Florida_copy.omd'
    newomdPath = '/Users/davidarmah/Documents/omf/omf/data/Model/admin/Automated Testing of resilientCommunity/color_test.omd'
    geo.map_omd(newomdPath, './', open_browser=True)
    


    
def new(modelDir):
    omdfileName = 'iowa240_in_Florida_copy2'

    defaultInputs = {
		"modelType": modelName,
		"inputDataFileName": omdfileName + '.omd',
        "feederName1": omdfileName,
        "lines":'Yes',
        "transformers":'Yes',
        "buses":'Yes',
        "fuses":'Yes',
        "loadCol": "Base Criticality Index",
        "refresh": False,
        "inputDataFileContent": 'omd',
        "optionalCircuitFile" : 'on',
		"created":str(datetime.datetime.now())
	}
    creationCode = __neoMetaModel__.new(modelDir, defaultInputs)
    try:
        shutil.copyfile(pJoin(__neoMetaModel__._omfDir, "static", "publicFeeders", defaultInputs["feederName1"]+'.omd'), pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
    except:
        return False
    return creationCode

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
	print("test")
    #test()
	#tests()
