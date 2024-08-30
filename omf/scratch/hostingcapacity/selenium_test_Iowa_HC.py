import time
import sys

from pathlib import Path

import omf

# Selenium Imports

def login_to_OMF( driver, username, password ):
  from selenium.webdriver.common.keys import Keys
  from selenium.webdriver.common.by import By


  username_field = driver.find_element(by=By.ID, value="username")
  password_field = driver.find_element(by=By.ID, value='password')
  username_field.send_keys(username)
  password_field.send_keys(password)
  password_field.send_keys(Keys.RETURN)



def firefox_test( url ):
  firefox_geckodriver_path = "/snap/bin/firefox"
  firefox_options = webdriver.FirefoxOptions()
  driver_service = webdriver.FirefoxService(executable_path=firefox_geckodriver_path)

  driver = webdriver.Firefox(service=driver_service, options=firefox_options)
  driver.get( url )

  time.sleep(2)
  driver.quit()

def chrome_test_iowa_state_algo( url, username, password ):
  from selenium import webdriver
  from selenium.webdriver.common.by import By
  from selenium.webdriver.common.keys import Keys
  from selenium.webdriver.support.select import Select
  from selenium.webdriver.support.ui import WebDriverWait
  from selenium.webdriver.support import expected_conditions

  retVal = True

  test_name = "Selenium Test for Hosting Capacity Iowa State Algorithm"
  modelDir = Path( omf.omfDir, "data", "Model", username, test_name )

  iowa_state_input = 'input_ISUTestData.csv'
  default_name = 'input_mohcaCustom.csv'

  # TODO: Do I want to check if the automated test exists already and if so, delete it?

  driver = webdriver.Chrome()
  driver.get( url )

  login_to_OMF( driver, username, password )
  
  # Create hostingCapacity Model
  driver.find_element(by=By.ID, value="newModelButton").click()
  driver.find_element(by=By.XPATH, value="//a[contains(@href, 'hostingCapacity')]" ).click()

  # Not sure if waiting one second for the pop-up for the name is needed
  wait = WebDriverWait(driver, 1)
  alert = wait.until(expected_conditions.alert_is_present())

  alert.send_keys(test_name)
  alert.accept()

  # Wait for model to load up
  # wait = WebDriverWait(driver, 3)  # Adjust the timeout as needed
  wait.until(expected_conditions.staleness_of(driver.find_element(By.TAG_NAME, "html")))

  # Upload Iowa State Input File
  ami_data_input = driver.find_element(by=By.ID, value="AMIDataFile")
  # Input must be of type string and be the absolute path to the file
  ami_data_input.send_keys( str( Path( omf.omfDir, 'static', 'testFiles', 'hostingCapacity', iowa_state_input).resolve() ) )
  
  # Set Algorithm
  algo_type_dropdown = driver.find_element(By.ID, 'algorithm')
  select = Select(algo_type_dropdown)
  select.select_by_visible_text('iastate')

  # Turn Traditional Hosting Cap Off
  trad_algo_dropdown = driver.find_element(By.ID, 'optionalCircuitFile')
  select = Select(trad_algo_dropdown)
  select.select_by_visible_text('Off')

  time.sleep(3) 

  driver.find_element(by=By.ID, value="runButton").click()

  #Can check for raw output and see if that is a good source to determine completion?

  userAMIDisplayFileName = driver.find_element(by=By.ID, value="userAMIDisplayFileName")
  newFileUploadedName = userAMIDisplayFileName.get_attribute('value')

  # Check if the HTML updates with the new file name that the user uploaded
  try:
    assert newFileUploadedName == iowa_state_input
    # DELETE print( newFileUploadedName + " " + voltageTestFile1)
  except AssertionError:
    print( "FAILED: Assertion that the HTML display name of the AMI Data input file correctly changed to the users file name")
    print( "Actual: " + newFileUploadedName + " Expected: " + iowa_state_input )
    retVal = False 
  
  #Check if the file is present in the directory with the correct standard naming convention name
  if Path( modelDir, default_name).exists() == False:
    print( default_name + " does not exist in the directory")
    retVal = False

  #Check to make sure that a file by the name the user uploaded is NOT there
  if Path( modelDir, iowa_state_input ).exists():
    print( "File created with users file input name: " + iowa_state_input )
    retVal = False

  # TODO: Check outputs - p vague idea
  # One idea - check if the raw input/output files exists. I think that's present for every algorithm after completion.
  WebDriverWait(driver, 600).until(expected_conditions.presence_of_element_located((By.ID, 'rawOutput')))

  driver.quit()
  return retVal

if __name__ == '__main__':
  url = 'http://localhost:5000/'
  if len( sys.argv ) != 3:
    print("Usage: python script.py <username> <password>")
    sys.exit(1)

  username = sys.argv[1]
  password = sys.argv[2]

  if chrome_test_iowa_state_algo( url, username, password ):
    print( "PASSED: Hosting Capacity Iowa State Algorithm")
  #firefox_test