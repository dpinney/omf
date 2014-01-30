## stuff to know for later -mh
# http://maps.googleapis.com/maps/api/geocode/json?address=psc&sensor=false
# http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3/by_state_and_city.html gives a list of TMY3 sources
# http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3/TMY3_StationsMeta.csv has the metadata for those TMY3 sources

## geocoding stuff
# http://airportcode.riobard.com/airport/GEG?fmt=JSON
# airportcode does not include lat/long
#zomg http://stackoverflow.com/questions/13104136/iata-to-country-api
# http://www.freebase.com/aviation/airport?schema=
# https://developers.google.com/accounts/docs/OAuth2
## tmy3 data sources near...
# http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3/
# http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3/TMY3_StationsMeta.csv
# http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3/690150TY.csv

import json
import urllib
import os
import csv
import math
import datetime
from datetime import datetime

# GetPeakSoalr(airport, dir=None)
#   a method to get the peak non-cloudy solar data from a locale.  takes the ten most solar-energetic days and averages
#   the values out into one 24-hour TMY3 file.
# @param airport    the airport code to look for solar data near
# @param dir        the directory to write the files into

def GetPeakSolar(airport, dir=None, metaFileName="TMY3_StationsMeta.csv", dniScale=1.0, dhiScale=1.0, ghiScale=1.0):
    if airport == None:
        #error
        return None
    smPsf = 10.7639104 # square feet ~ source Google
    api_key = 'AIzaSyDR9Iwhp1xbs31c6FpO-5g0bdEXCyN1JL8'
    service_url = 'https://www.googleapis.com/freebase/v1/mqlread'
    query = [{'id':None, 'name':None, 'type': '/aviation/airport', 'iata' : airport,
              '/location/location/geolocation' : [{'latitude' : None, 'longitude':None, 'elevation':None}]
              }]
    currDir = os.getcwd()
    params = {'query' : json.dumps(query), 'key' : api_key}
    url = service_url + '?' + urllib.urlencode(params)
    
    # query Freebase for specified IATA airport code
    response = json.loads(urllib.urlopen(url).read())
    #print(response)
    
    # if zero results, fail
    if len(response['result']) == 0:
        print("Failed to return any airport locations")
        return None
    # if more than one result, get first one
    if len(response['result']) > 1:
        print("Multiple airport results (strange!), using the first result")
    
    # get GPS from result
    lat = response['result'][0]['/location/location/geolocation'][0]['latitude']
    long = response['result'][0]['/location/location/geolocation'][0]['longitude']
    #print('Airport \'{}\' located at ({}, {})'.format(airport, str(lat), str(long)))
    # look for metadata file
    metafile = None
    if os.path.isdir(dir):
        os.chdir(dir)
    if not os.path.isfile(metaFileName):
        address = 'http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/tmy3/TMY3_StationsMeta.csv'
        urllib.urlretrieve(address, metaFileName) # if this fails, we let it break.
    metaFile = open(metaFileName)
    os.chdir(currDir)
    
    # parse metadata file
    # * "USAF","Site Name","State","Latitude","Longitude","TZ","Elev","Class","Pool"
    metaFileReader = csv.reader(metaFile, delimiter=',')
    metaFileRows = [line for line in metaFileReader] # NOTE: first line is headers.
    metaHeaders = metaFileRows.pop(0)
    
    # find our desired column indices
    latItem = next(x for x in metaHeaders if 'Latitude' in x)
    longItem = next(x for x in metaHeaders if 'Longitude' in x)
    idItem = next(x for x in metaHeaders if 'USAF' in x)
    latIndex = metaHeaders.index(latItem)
    longIndex = metaHeaders.index(longItem)
    idIndex = metaHeaders.index(idItem)
    
    stationDist = []
    for row in metaFileRows:
        try:
            x = float(row[latIndex]) - lat
            y = float(row[longIndex]) - long
            stationDist.append((x*x+y*y, row[idIndex]))
        except:
            pass # 'bad' line
        
    # find nearest station based on metadata CSV
    minDist = min([line[0] for line in stationDist])
    stationResult = [line[1] for line in stationDist if line[0] == minDist]
    #print("Found station: "+str(stationResult))
    stationId = stationResult[0] # ID string from the first result
    
    # check if peak data exists for specified location
    if os.path.isdir(dir):
        os.chdir(dir)
    if os.path.isfile("solar_{}_winter.csv".format(airport)):
        #  * if yes, return true ~ already done here
        os.chdir(currDir)
        return airport
    
    # get specified TMY csv file
    tmyURL = 'http://rredc.nrel.gov/solar/old_data/nsrdb/1991-2005/data/tmy3/'+stationId+'TY.csv'
    #print("station URL: "+tmyURL)
    tmyResult = urllib.urlretrieve(tmyURL, stationId+'TY.csv')
    tmyFile = open(tmyResult[0])
    os.chdir(currDir)
    tmyReader = csv.reader(tmyFile, delimiter=',')
    tmyLines = [line for line in tmyReader]
    tmyHeader = tmyLines.pop(0)   # "727845,"PASCO",WA,-8.0,46.267,-119.117,136"
    tmyColumns = tmyLines.pop(0)  # "Date (MM/DD/YYYY),Time (HH:MM),ETR (W/m^2),ETRN (W/m^2),GHI (W/m^2),GHI source,GHI uncert (%),DNI (W/m^2),DNI source,DNI uncert (%),
    #                             #  DHI (W/m^2),DHI source,DHI uncert (%),GH illum (lx),GH illum source,Global illum uncert (%),DN illum (lx),DN illum source,DN illum uncert (%),
    #                             #  DH illum (lx),DH illum source,DH illum uncert (%),Zenith lum (cd/m^2),Zenith lum source,Zenith lum uncert (%),TotCld (tenths),TotCld source,
    #                             #  TotCld uncert (code),OpqCld (tenths),OpqCld source,OpqCld uncert (code),Dry-bulb (C),Dry-bulb source,Dry-bulb uncert (code),Dew-point (C),
    #                             #  Dew-point source,Dew-point uncert (code),RHum (%),RHum source,RHum uncert (code),Pressure (mbar),Pressure source,Pressure uncert (code),
    #                             #  Wdir (degrees),Wdir source,Wdir uncert (code),Wspd (m/s),Wspd source,Wspd uncert (code),Hvis (m),Hvis source,Hvis uncert (code),
    #                             #  CeilHgt (m),CeilHgt source,CeilHgt uncert (code),Pwat (cm),Pwat source,Pwat uncert (code),AOD (unitless),AOD source,AOD uncert (code),
    #                             #  Alb (unitless),Alb source,Alb uncert (code),Lprecip depth (mm),Lprecip quantity (hr),Lprecip source,Lprecip uncert (code)"
    # 01/01/2000,01:00,0,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,0,2,0,6,E,9,3,E,9,-2.0,A,7,-2.0,A,7,100,A,7,997,A,7,0,A,7,0.0,A,7,8000,A,7,77777,A,7,1.0,E,8,0.051,F,8,0.400,F,8,-9900,-9900,?,0
    seasonDict = {1 : "Winter", 2 : "Winter", 3 : "Spring", 4 : "Spring", 5 : "Spring", 6 : "Summer", 7 : "Summer", 8 : "Summer", 9 : "Fall", 10 : "Fall", 11 : "Fall", 12 : "Winter"}
    seasonList = ["Winter", "Spring", "Summer", "Fall"]
    
    #print(tmyColumns)
    dateItem = next(x for x in tmyColumns if 'Date' in x)
    ghiItem = next(x for x in tmyColumns if 'GHI (W/m^2)' in x)
    dniItem = next(x for x in tmyColumns if 'DNI (W/m^2)' in x)
    dhiItem = next(x for x in tmyColumns if 'DHI (W/m^2)' in x)
    dateIndex = tmyColumns.index(dateItem)
    ghiIndex = tmyColumns.index(ghiItem)
    dniIndex = tmyColumns.index(dniItem)
    dhiIndex = tmyColumns.index(dhiItem)
    
    dateFormat = "%m/%d/%Y"
    dayDict = {}
    for line in tmyLines:
        lineDate = datetime.strptime(line[dateIndex], dateFormat)
        if lineDate in dayDict:
            dayDict[lineDate].append(line)
        else:
            dayDict[lineDate] = [line]
    # each entry in dayDict is now a 24-item list 
    
    energyDict = {}
    for season in seasonList:
        energyDict[season] = []
    for key in dayDict: # for each day,
        day = dayDict[key]
        # calculate
        dhi = [float(value[dhiIndex]) for value in day]
        dni = [float(value[dniIndex]) for value in day]
        ghi = [float(value[ghiIndex]) for value in day]
        values = (math.fsum(dni), math.fsum(dhi), math.fsum(ghi))
        energy = values[0] * dniScale + values[1] * dhiScale + values[2] * ghiScale
        season = seasonDict[key.month]
        energyDict[season].append((key, (dni, dhi, ghi), energy))
        
    # for each of four seasons,
    solarHeader = "Time(HH:MM),GHI_Normal,DNI_Normal,DHI_Normal\n"
    for season in seasonList:
        data = sorted(energyDict[season], key=lambda dayItem: dayItem[2]) # sort by energy
        #  * pick out top 10 days
        topDays = data[-10:] 
        #  * write file with average of those ten days
        tDni = [0.0] * 25
        tDhi = [0.0] * 25
        tGhi = [0.0] * 25
        for day in topDays:
            dni, dhi, ghi = day[1]
            for i in range(len(dni)):
                tDni[i] += dni[i]
                tDhi[i] += dhi[i]
                tGhi[i] += ghi[i]
        # write average day to file
        fileName = "solar_{}_{}.csv".format(airport, season.lower())
        if os.path.isdir(dir):
            os.chdir(dir)
        outFile = open(fileName, "w")
        os.chdir(currDir)
        # Time(HH:MM), GHI_Normal, DNI_Normal and DHI_Normal
        outFile.write(solarHeader)
        for i in range(24):
            outFile.write("{}:00,{},{},{}\n".format(str(i), str(tGhi[i]/10/smPsf), str(tDni[i]/10/smPsf), str(tDhi[i]/10/smPsf) ) )        
        outFile.close()
    os.chdir(currDir)
    return airport

