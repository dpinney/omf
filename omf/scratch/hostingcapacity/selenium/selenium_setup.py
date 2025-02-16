from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException

def login_to_OMF( driver, username, password ):
  username_field = driver.find_element(by=By.ID, value="username")
  password_field = driver.find_element(by=By.ID, value='password')
  username_field.send_keys(username)
  password_field.send_keys(password)
  password_field.send_keys(Keys.RETURN)
  
def delete_old_instance( driver, username, test_name ):
	href_model = "./model/" + username + "/" + test_name
	try:
		existing_model = driver.find_element(by=By.XPATH, value='//a[@href="'+ href_model +'"]')
	except NoSuchElementException:
		return False
	if existing_model.is_displayed():
		existing_model.click()
		deleteButton = driver.find_element(by=By.ID, value="deleteButton")
		deleteButton.click()
		wait = WebDriverWait(driver, 1)
		alert = wait.until(expected_conditions.alert_is_present())
		alert.accept()
		return True
	return False

