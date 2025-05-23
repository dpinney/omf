# Selenium Imports

import test_selenium_hostingCapacity

if __name__ == "__main__":
	url = 'http://0.0.0.0:5000/'
	username, password = "admin", "admin"
	if ( test_selenium_hostingCapacity.hostingCapacityDoubleWarnings( url, username, password ) == False ):
		print("FAIL :: test_selenium_hostingCapacity.hostingCapacityDoubleWarnings")
	if ( test_selenium_hostingCapacity.hostingCapacityVoltVar( url, username, password ) == False ):
		print("FAIL :: test_selenium_hostingCapacity.hostingCapacityVoltVar")
	if ( test_selenium_hostingCapacity.hostingCapacityReactivePowerWarning( url, username, password ) == False ):
		print("FAIL :: test_selenium_hostingCapacity.hostingCapacityReactivePowerWarning")





