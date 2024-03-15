import time
import sys

from pathlib import Path

import omf

# Selenium Imports

def firefox_test( url ):
  firefox_geckodriver_path = "/snap/bin/firefox"
  firefox_options = webdriver.FirefoxOptions()
  driver_service = webdriver.FirefoxService(executable_path=firefox_geckodriver_path)

  driver = webdriver.Firefox(service=driver_service, options=firefox_options)
  driver.get( url )

  time.sleep(2)
  driver.quit()

def chrome_test( url, username, password ):
  from selenium import webdriver
  from selenium.webdriver.common.by import By
  from selenium.webdriver.common.keys import Keys
  from selenium.webdriver.support.select import Select
  from selenium.webdriver.support.ui import WebDriverWait
  from selenium.webdriver.support import expected_conditions

  retVal = True

  test_name = "Selenium Test for Transformer Pairing Voltage File Submission"
  modelDir = Path( omf.omfDir, "data", "Model", username, test_name )

  defaultVoltageFileName = "voltageData_AMI.csv"
  voltageTestFile1 = "uploadVoltage1.csv"
  voltageTestFile1Value = 2.1
  voltageTestFile2 = "uploadVoltage2.csv"
  voltageTestFile2Value = 2.2

  # TODO: Do I want to check if the automated test exists already and if so, delete it?

  driver = webdriver.Chrome()
  driver.get( url )

  # Login to OMF
  username_field = driver.find_element(by=By.ID, value="username")
  password_field = driver.find_element(by=By.ID, value='password')
  username_field.send_keys(username)
  password_field.send_keys(password)
  password_field.send_keys(Keys.RETURN)

  # Create transformerPairing Model
  driver.find_element(by=By.ID, value="newModelButton").click()

  ## find transformerPairing Model using xpath 
  #transformerPairingModelButton = driver.find_element(by=By.XPATH, value="//a[contains(@href, 'transformerPairing')]" )
  # transformerPairingModelButton.click()
  #driver.execute_script("arguments[0].click();", transformerPairingModelButton)
  driver.find_element(by=By.XPATH, value="//a[contains(@href, 'transformerPairing')]" ).click()

  alert = wait.until(expected_conditions.alert_is_present())

  alert.send_keys(test_name)
  alert.accept()

  wait = WebDriverWait(driver, 5)  # Adjust the timeout as needed
  wait.until(expected_conditions.staleness_of(driver.find_element(By.TAG_NAME, "html")))

  voltage_file_input = driver.find_element(by=By.ID, value="voltageDataFile")
  # Input must be of type string and be the absolute path to the file
  voltage_file_input.send_keys( str( Path(voltageTestFile1).resolve() ) )\

  driver.find_element(by=By.ID, value="runButton").click()

  # Wait?

  time.sleep(5)

  userInputVoltageDisplayName = driver.find_element(by=By.ID, value="userInputVoltageDisplayName")
  newFileUploadedName = userInputVoltageDisplayName.get_attribute('value')

  # Check if the HTML updates with the new file name that the user uploaded
  try:
    assert newFileUploadedName == voltageTestFile1
    # DELETE print( newFileUploadedName + " " + voltageTestFile1)
  except AssertionError:
    print( "FAILED: Assertion that the HTML display name of the voltage file correctly changed to the users file name")
    print( "Actual: " + newFileUploadedName + " Expected: " + voltageTestFile1 )
    retVal = False 
  
  #Check if the file is present in the directory with the correct standard naming convention name
  if Path( modelDir, defaultVoltageFileName).exists() == False:
    print( defaultVoltageFileName + " does not exist in the directory")
    retVal = False

  #Check to make sure that a file by the name the user uploaded is NOT there
  if Path( modelDir, voltageTestFile1 ).exists():
    print( "File created with users file input name: " + voltageTestFile1 )
    retVal = False

  #Check if the file is the new modified file
  with open( Path(modelDir, defaultVoltageFileName), 'r' ) as voltage1:
    first_line = voltage1.readline()
    values = first_line.split(',')
        
    # Strip any leading/trailing whitespace from each value
    values = [value.strip() for value in values]
    firstValue = values[0]
    try:
      assert float(firstValue) == float(voltageTestFile1Value)
    except AssertionError:
      print( "FAILED: Assertion that the " +  defaultVoltageFileName + " is the correct uploaded file")
      print( "Actual: " + str(firstValue) + " Expected: " + str(voltageTestFile1Value) )
      retVal = False

  # TODO: Check outputs - p vague idea
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

  if chrome_test( url, username, password ):
    print( "PASSED: Single File Upload for Transformer Pairing Chrome Test")
  #firefox_test