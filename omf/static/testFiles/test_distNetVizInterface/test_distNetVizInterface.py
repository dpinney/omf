import time
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options


def _get_logged_in_browser():
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
    olin_barre_gh.click() # This opens a new tab, but selenium is still in the original tab
    time.sleep(5)
    return browser


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

class Test_AdminUser:

    def test_adminUser_canViewPublicModel(self):
        pass

    def test_adminUser_canViewAdminModel(self):
        pass

    def test_adminUser_canViewRegularUserModel(self):
        pass

class Test_RegularUser:

    def test_regularUser_canViewPublicModel(self):
        pass

    def test_regularUser_canViewRegularUserModel(self):
        pass

    def test_regularUser_canViewSharedModel(self):
        pass

'''THIS IS NOT WORKING 2/14/20'''
class Test_JasmineTests:
    def test_jasmineTests_successfullyRun(self):
        browser = _get_logged_in_browser()
        tabs = browser.window_handles
        browser.switch_to.window(tabs[1])
        # I should be able to simply create and load the jasmine script files in the proper order, but when I do normally, I get "jasmineRequire" not
        # defined. This goes away if I sleep after loading jasmine.js ¯\_(ツ)_/¯
        # - I think the problem is that the jasmine scripts need to be loaded into <head> BEFORE the rest of the document is parsed. There doesn't
        #   seem to be a way to "reload the page with new inserted scripts" in JS, so I'll need ANOTHER helper script that ...
        #   - But the point is that I don't want a helper script. Selenium is supposed to test the page using a full, normal integration test
        browser.execute_script('\
        \
        \
        function sleep(ms) {\
            return new Promise(resolve => setTimeout(resolve, ms));\
        }\
        async function load_other_jasmine_files() {\
        \
            s = document.createElement("script");\
            s.setAttribute("src", "/static/testFiles/test_distNetVizInterface/spec_distNetVizInterface.js");\
            s.setAttribute("type", "text/javascript");\
            document.body.append(s);\
        }\
        load_other_jasmine_files();\
        ')
        while True:
            pass


if __name__ == '__main__':
    #view_public_feeder_as_user()
    t = Test_JasmineTests()
    t.test_jasmineTests_successfullyRun()
        #let s = document.createElement("link");\
        #s.setAttribute("rel", "stylesheet");\
        #s.setAttribute("href", "/static/testFiles/test_distNetVizInterface/jasmine-3.3.0/jasmine.css");\
        #document.head.append(s);\
        #s = document.createElement("script");\
        #s.setAttribute("src", "/static/testFiles/test_distNetVizInterface/jasmine-3.3.0/jasmine.js");\
        #s.setAttribute("type", "text/javascript");\
        #document.head.append(s);\

            #await sleep(2000);\
            #let s = document.createElement("script");\
            #s.setAttribute("src", "/static/testFiles/test_distNetVizInterface/jasmine-3.3.0/jasmine-html.js");\
            #s.setAttribute("type", "text/javascript");\
            #document.head.append(s);\
            #await sleep(2000);\
            #s = document.createElement("script");\
            #s.setAttribute("src", "/static/testFiles/test_distNetVizInterface/jasmine-3.3.0/boot.js");\
            #s.setAttribute("type", "text/javascript");\
            #document.head.append(s);\
            #await sleep(2000);\
