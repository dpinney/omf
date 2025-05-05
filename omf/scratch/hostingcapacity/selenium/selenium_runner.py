# Selenium Imports

import test_selenium_hostingCapacity

if __name__ == "__main__":
	url = 'http://0.0.0.0:5000/'
	username, password = "admin", "admin"
	test_selenium_hostingCapacity.hostingCapacityDoubleWarnings( url, username, password )	
	test_selenium_hostingCapacity.hostingCapacityVoltVar( url, username, password )





