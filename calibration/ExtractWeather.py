# ExtractWeather.py
# @author Matt Hauer
#

import cmath
import math
import random
import datetime
import os
from datetime import timedelta
from datetime import datetime
#import urllib.request #python 3.0 splits into request, parse, and error.
import urllib

def IsLeapyear(year):
    if (year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0)):
        return True
    return False

def GetWeather(start, end, airport, dir='temp', startYear = 2012):
    if start is None:
        print("ERROR: no start date given!")
        return None
    if end is None:
        print("ERROR: no end date given!")
        return None
    if airport is None:
        print("ERROR: no airport code given!")
        return None
    # static data
    days_in_month = {"Jan" : 31, "Feb" : 28,
                     "Mar" : 31, "Apr" : 30,
                     "May" : 31, "Jun" : 30,
                     "Jul" : 31, "Aug" : 31,
                     "Sept" : 30, "Oct" : 31,
                     "Nov" : 30, "Dec" : 31}
    # initializers from Matlab script
    currDir = os.getcwd()
    year = startYear
    month = 1
    day = 1
    num_days = 0
    start_dt = datetime.today() # bogus initial value
    end_dt = datetime.today() + timedelta(days = 1) # bogus initial value
    # parse start and end dates
    try:
        start_dt = datetime.strptime(start, "%m-%d-%Y")
    except ValueError as ve:
        print("ERROR: start date '" + start + "' was not in mm-dd-yyyy format!")
        return None
    if end is not None:
        try:
            end_dt = datetime.strptime(end, "%m-%d-%Y")
        except ValueError as ve:
            print("ERROR: end date '" + end + "' was not in mm-dd-yyyy format!")
            return None
    else:
        end_dt = start_dt + timedelta(days = 30) 
    # calculate the number of days to fetch
    num_days = (end_dt - start_dt).days
    work_dir = None
    work_day = start_dt
    if os.path.isdir(dir):
        os.chdir(dir)        
    one_day = timedelta(days = 1)
    for i in range(num_days):
        # explicitly extract pieces
        year = work_day.year
        month = work_day.month
        day = work_day.day
        # generate URL and get data
        # http://www.wunderground.com/history/airport/NYC/2012/6/7/DailyHistory.html?req_city=NA&reqstate=NA&req_statename=NA&format=1
        address = "http://www.wunderground.com/history/airport/{}/{:d}/{:d}/{:d}/DailyHistory.html?req_city=NA&reqstate=NA&req_statename=NA&format=1".format(airport, year, month, day)
        filename = "weather_{}_{:d}_{:d}_{:d}.csv".format(airport, year, month, day)
        if os.path.isfile(filename):
            continue # we have the file already, don't re-download it.
        try:
            #f = urllib.request.urlretrieve(address, filename) # v3.0
            f = urllib.urlretrieve(address, filename) # v2.7
            #print("got data from "+address)
        except:
            print("ERROR: unable to get data from URL '"+address+"'")
            return None
        # advance one day
        work_day = work_day + one_day # yes, it handles leap years!
    os.chdir(currDir) # revert to previous path
    return 0 # good

def main():
    #tests here
    res = GetWeather('3-01-2010', '5-1-2010', airport='PDX', dir='c:/projects/temp')
    
if __name__ == '__main__':
    main()
# EOF

#http://www.wunderground.com/history/airport/PDX/2010/6/21/DailyHistory.html?req_city=NA&reqstate=NA&req_statename=NA&format=1
