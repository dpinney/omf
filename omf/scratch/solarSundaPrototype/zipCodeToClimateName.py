import json, os, sys, tempfile, math
import csv, math

def zipCodeToclimateName(zipCode):
	def compareLatLon(LatLon, LatLon2):
		differenceLat = float(LatLon[0]) - float(LatLon2[0]) 
		differenceLon = float(LatLon[1]) - float(LatLon2[1])
		distance = math.sqrt(math.pow(differenceLat, 2) + math.pow(differenceLon,2))
		return distance

	#only has A,  and V
	def safeListdir(path):
		try: return os.listdir(path)
		except:	return []

	climateNames = [x[:-5] for x in safeListdir("../../data/Climate/")]
	print "ClimateNames: ", climateNames
	climateCity = []
	lowestDistance = 1000


	try:
		#Parse .csv file with city/state zip codes and lat/lon
		print "Input zipcode: ", zipCode
		print "\nFirst looking for state, city, and lat/lon:"	
		with open('C:\Users\Asus\Documents\GitHub\NRECA\omf\omf\data\Climate\zip_codes_states.csv', 'rt') as f:
		     reader = csv.reader(f, delimiter=',') 
		     for row in reader:
		          for field in row:
		              if field == zipCode:
		                  #print "field", row
		                  zipState = row[4] 
		                  zipCity = row[3]
		                  print "    State_City: ", zipState + "_" + zipCity
		                  ziplatlon  = row[1], row[2]
		                  print "    Lat/Lon: ", ziplatlon

		#Looks for climate data by looking at all cities in that state
		#Should be change to check other states too 
		print "\nNow looking for City matches in  that state that we have climate data for:"
		#Filter only the cities in that state
		for x in range(0, len(climateNames)):	
			if (zipState+"-" in climateNames[x]):
				climateCity.append(climateNames[x])	
		climateCity = [w.replace(zipState+"-", '') for w in climateCity]	
		'''
		#Use all the cities in all states, could be only current state + neighboring states
		zipStates = ["AK", "AL", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD", "ME", "VA"]
		for x in range (0, len(zipStates)):
			climateNames = [w.replace(zipStates[x]+"-", '') for w in climateNames]
		climateCity = climateNames
		'''					
		print "    Climate Cities found:", climateCity	
	    #Parse the cities distances to zipcode city to determine closest climate
		print "\nNow matching closest city by lat/lon:"
		for x in range (0,len(climateCity)):	
			print "    \nCity: ", climateCity[x]				
			with open('C:\Users\Asus\Documents\GitHub\NRECA\omf\omf\data\Climate\zip_codes_states.csv', 'rt') as f:
				reader = csv.reader(f, delimiter=',') 
				for row in reader:
					if ((row[4].lower() == zipState.lower()) and (row[3].lower() == str(climateCity[x]).lower())):
						climatelatlon  = row[1], row[2]          					#print "row3", row[3].lower(), "climatecity", climateCity[0].lower()#print "    city: "row[3].lower()          	
	                	print "    Comparing latlon: ", climatelatlon     
	                	print "                  to: ", ziplatlon

	                	distance = compareLatLon(ziplatlon, climatelatlon)                	
	                	if (distance < lowestDistance):
	                		lowestDistance = distance
	                		print "    New Lowest Distance : ", lowestDistance, "\n                Found at: ", climatelatlon, ", City: ", climateCity[x]
	                		found = x	
		climateName = zipState + "-" + climateCity[found]
		return climateName
	except:
		print 
		print "----------------------------------------------"
		print "Failed to find zipcode in climate data"
		return "NULL"


def _tests():	
	inData = {"zipCode": "24501"}
	climateName = zipCodeToclimateName(inData["zipCode"])	
	print "\nclimateName returned: ", climateName	

if __name__ == '__main__':
	_tests()

	'''		'''