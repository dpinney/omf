WindScript
author: Matt Hauer (matthew.hauer@pnl.gov)
for the OMF project

v01 - 24 June 2013 - MH - initial version

Contents:
 * ProcessWeather.py
 * ExtractWeather.py
 
Methods:
	ProcessWeather.ProcessWeather(start, end, airport='', dir='.', interpolate="linear")
	ProcessWeather.GenerateWeatherFiles(start, end, airport, dir='')
	ExtractWeather.GetWeather(start, end, airport, dir='temp', startYear = 2012)
	GetPeakSolar.GetPeakSolar(airport, dir=None, metaFileName="TMY3_StationsMeta.csv", dniScale=1.0, dhiScale=1.0, ghiScale=1.0)

Short How-To:
	GenerateWeatherFiles('6-1-2010', '8-1-2010', 'PSC', dir='temp') will first call ExtractWeather.GetWeather(), then ProcessWeather.ProcessWeather().
	
Longer How-To:
	ExtractWeather.GetWeather('6-1-2010', '8-1-2010', 'PSC', dir='temp', startYear = 2012) will direct the check for the existence of a set of files with the naming convention "weather_[airport]_[YYYY]_[MM]_[DD].csv" in the "dir" path.  Any files that are not found will be downloaded from wunderground.com.  The start and end dates must be in 'MM-DD-YYYY' format.  If a None end date is supplied, the script will default to 30 days.  The script will short-circuit and do nothing if the start date is after the end date.
	GetPeakSolar.GetPeakSolar('PSC') will look for the geocoordinates of the specified IATA airport code, locate the nearest TMY3 source from the NREL RREDC TMY3 station metadata file (downloading the file if it's not in 'dir'), download the associated TMY3 file if it isn't in 'dir', identify the ten days with the most solar energy for each of the four seasons, write "solar_[airport]_[season].csv" files, then return.  The method will short-circuit if "solar_[airport]_winter.csv" exists in 'dir'.
	ProcessWeather.ProcessWeather('6-1-2010', '8-1-2010', 'PSC', dir='temp') will verify that Wunderground weather files generated with EW.GetWeather()'s naming convention exist for the specified range (failing if not), will concatenate the values into one large list, identify the column names that the script is concerned with, will map non-numerical values to numerical values, will call GetPeakSolar() if "solar_[airport]_winter.csv" cannot be found, will read the typical solar values, will interpolate the read values into five-minute samples, then write all the interpolated samples into "SCADA_weather_[airport]_gld.csv" into the local directory.
	GenerateWeatherFiles('6-1-2010', '8-1-2010', 'PSC', dir='temp') will first call ExtractWeather.GetWeather(), then ProcessWeather.ProcessWeather().

Method interfaces:
	ProcessWeather.ProcessWeather(start, end, airport='', dir='.', interpolate="linear")
	 * start - "MM-DD-YYYY" string - the first day to retrieve weather information from
	 * end - "MM-DD-YYYY" string - the day (non-inclusive) to retrieve weather information until
	 * airport - string - the IATA airport code to look for weather and climate data for
	 * dir - string - the directory to check for data files in, and to cache downloaded files in
	 * interpolate - string {"none", "linear", "quadratic"} - the interpolation method to use for generating data points between known values
	 
	ProcessWeather.GenerateWeatherFiles(start, end, airport, dir='')
	 * start - "MM-DD-YYYY" string - the first day to retrieve weather information from
	 * end - "MM-DD-YYYY" string - the day (non-inclusive) to retrieve weather information until
	 * airport - string - the IATA airport code to look for weather and climate data for
	 * dir - string - the directory to check for data files in, and to cache downloaded files in
	 
	ExtractWeather.GetWeather(start, end, airport, dir='temp', startYear = 2012)
	* start - "MM-DD-YYYY" string - the first day to retrieve weather information from
	* end - "MM-DD-YYYY" string - the day (non-inclusive) to retrieve weather information until
	* airport - string - the IATA airport code to look for weather and climate data for
	* dir - string - the directory to check for data files in, and to cache downloaded files in
	* startYear - integer - unused
	
	GetPeakSolar.GetPeakSolar(airport, dir=None, metaFileName="TMY3_StationsMeta.csv", dniScale=1.0, dhiScale=1.0, ghiScale=1.0)
	* airport - string - the IATA airport code to look for weather and climate data for
	* dir - string - the directory to check for data files in, and to cache downloaded files in	
	* metaFileName - string - the name of the NREL RREDC TMY3 station metadata file to look for, locally and on the NREL site.
	* dniScale - float - the implicit bias to apply to direct normal input, for tuning purposes.
	* dhiScale - float - the implicit bias to apply to diffuse horizontal input, for tuning purposes.
	* ghiScale - float - the implicit bias to apply to global horizontal input, for tuning purposes.
	
Support:
	Email matthew.hauer@pnl.gov with questions, concerns, or bugs.
	Alternately, email jason.fuller@pnl.gov with the same.
	
Acknowledgements:
	Thank You goes out to the following-
	* Wunderground (www.wunderground.com) for their public weather information archives.
	* Freebase (www.freebase.com) for the airport database, included IATA codes and geolocations.
	* NREL (www.nrel.gov) and their Renewable Resource Data Center (www.nrel.gov/rredc) for publicly posting the TMY3 files