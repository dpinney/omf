import time
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


# TODO: 
# - a generic version of this function should be called with arguments!
# - I should call this function with every public feeder just to be sure. For example, if Olin Barre GH Battery was modified earlier, the browser
#   would have never tried to save, and an exception never would have been thrown! So much context!
def view_public_feeder_as_user():
    #opts = Options()
    #opts.set_headless()
    #assert opts.headless
    #browser = Chrome(options=opts)
    browser = Chrome()
    browser.get('http://localhost:5000')
    username_input = browser.find_elements_by_id('username')[0]
    username_input.send_keys('test')
    password_input = browser.find_elements_by_id('password')[0]
    password_input.send_keys('test')
    login_button = browser.find_elements_by_id('loginForm')[0].find_elements_by_tag_name('button')[0]
    login_button.click()
    demo_batter_olin_barre_gh_battery = browser.find_elements_by_link_text('Demo Batter Olin Barre GH Battery')[0]
    demo_batter_olin_barre_gh_battery.click()
    olin_barre_gh = browser.find_elements_by_id('feederButton')[1]
    olin_barre_gh.click()
    time.sleep(5)
    browser_errors = []
    for log in browser.get_log('browser'):
        if log['level'] == 'SEVERE':
            browser_errors.append(log)
    if len(browser_errors) > 0:
        raise Exception(f'Test failed: {browser_errors}')
    while True:
        pass


if __name__ == '__main__':
    view_public_feeder_as_user()
