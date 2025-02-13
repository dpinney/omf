import sys
from selenium import webdriver
from pathlib import Path

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

# Non-Python Imports
import selenium_setup
import omf

# Chrome, in the future I want to make firefox ones because I use firefox :D

def hosting_capacity_double_warnings_test_full(url, username, password):
	'''
	Hosting Capacity Selenium Test None as Q
	- File contains reactive power column with all None values
	- File contains buses that are not in circuit

	Test ensures:
	- Sandia's algorithm works with reactive power as none
	- both warnings show up, not just 1
	- Map is still there even though there's no colorby
	- Both model-based and downline load coloring still there #TODO:
	'''

	success = False
	test_name = "Selenium Test Hosting Capacity reactive power as nones"
	modelDir = Path( omf.omfDir, "data", "Model", username, test_name )
	testFile = "doc - input_mohcaCustom_NoneQ.csv"

	driver = webdriver.Chrome()
	driver.get( url )
	wait = WebDriverWait(driver, 1)
	selenium_setup.login_to_OMF(driver, username=username, password=password)

  # TODO: Do I want to check if the automated test exists already and if so, delete it?
	deleted = selenium_setup.delete_old_instance(driver, username=username, test_name=test_name)

	if deleted:
		wait.until(expected_conditions.element_to_be_clickable((By.ID, "newModelButton")))	

	# Create hostingCapacity Model
	driver.find_element(by=By.ID, value="newModelButton").click()
	driver.find_element(by=By.XPATH, value="//a[contains(@href, 'hostingCapacity')]" ).click()

	# Not sure if waiting one second for the pop-up for the name is needed
	alert = wait.until(expected_conditions.alert_is_present())

	# Submit the test name 
	alert.send_keys(test_name)
	alert.accept()

	# Wait until the page loads up
	wait.until(expected_conditions.staleness_of(driver.find_element(By.TAG_NAME, "html")))

	# Upload NoneQ File
	model_free_data_input = driver.find_element(by=By.ID, value="AMIDataFile")
	model_free_data_input.send_keys( str( Path("./", testFile).resolve() ) )

	# Run model
	driver.find_element(by=By.ID, value="runButton").click()

	# Wait 60 seconds for the model to run. I hate this timeout thing.	
	WebDriverWait(driver, 60).until(expected_conditions.presence_of_element_located((By.ID, 'rawOutput')))

	# Testing Part
	# Check for warnings
	reactive_power_warning = driver.find_element(by=By.ID, value="reactivePowerWarningInformation")
	try:
		assert( reactive_power_warning.is_displayed() == True )
	except AssertionError:
		print("FAILED: Warning Missing from Outputs :: Model Free Reactive Power :: htmlElement reactivePowerWarningInformation")

	buses_mia_warning = driver.find_element(by=By.ID, value="mapWarningInformation")
	try:
		assert( buses_mia_warning.is_displayed() == True )
	except AssertionError:
		print("FAILED: Warning Missing from Outputs :: Buses between files are different -> compromised map :: htmlElement mapWarningInformation")

	# Make sure map is still there
	map = driver.find_element(by=By.ID, value="hostingCapacityMap")
	try:
		assert( map.is_displayed() == True )
	except AssertionError:
		print("FAILED: Map is missing from outputs")
	
	driver.quit()
	success = True

	return success

if __name__ == "__main__":
	url = 'http://0.0.0.0:5000/'
	# if len( sys.argv ) != 3:
	# 	print("Usage: python3 script.py <username> <password>")
	# 	sys.exit(1)

	# username = sys.argv[1]
	# password = sys.argv[2]

	username = "admin"
	password = "admin"

	hosting_capacity_double_warnings_test_full(url, username, password)
