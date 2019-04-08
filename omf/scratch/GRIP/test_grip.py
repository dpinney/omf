'''
Start GRIP container, test the API endpoints.

TODO
XXX Docker build.
XXX Test interface.
XXX File handling backend and test.
XXX What routes? https://docs.google.com/presentation/d/17KTL5q3Nd8E_iUehLKGhCDZar8nkyn7hm8JOu6RMZ4Y/edit#slide=id.g389c95e613_0_15
XXX Implement a route.
XXX Implement the rest of the routes.
OOO Add an option to test against the container.
'''

#import webbrowser
import io, os, omf, grip, requests, pytest
from multiprocessing import Process

# Start the server.
#p = Process(target=grip.serve, args=())
#p.start()
# Shouldn't I join() here? Block the execution of the testing code until the server process finishes. Well, the server process never finishes.
# Can I send some kind of signal? I'll worry about that later. Just do something.

"""
Test format:
1) Expect a certain HTTP code
2) Exepct certain HTTP response
"""

@pytest.fixture
def client():
    # testing must be set to true on the Flask application
    grip.app.config['TESTING'] = True
    # create a test client with built-in Flask code
    client = grip.app.test_client()
    # 'yield' instead of 'return' due to how fixtures work in pytest
    yield client
    # Could put teardown code below if needed

class TestOneLineGridLab(object):

    def test_postRequest_returns_png(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        test_file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(test_file_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, filename),
            "useLatLons": False # big
            #"useLatLons": True
        }
        response = client.post("/oneLineGridlab", data=data)
        # Assert that it returned the correct code
        assert response.status_code == 200
        # Assert that it returned the correct type of file!!!
        assert response.mimetype == "image/png"
        assert response.content_length == 2579
        #response = requests.post(
        #    'http://localhost:5100/oneLineGridlab',
        #    files={
        #        'glm':open(test_glm_file).read()
        #    },
        #    data={
        #        'useLatLons':False
        #    }
        #)
    
    def test_bad_request(self, client):
        response = client.get("/oneLineGridlab")
        assert response.status_code == 400


"""
# Make sure it's up.
# webbrowser.open_new('http://localhost:5100/eatfile')
# Test a simple route.
response1 = requests.post('http://localhost:5100/eatfile', files={'test.txt':'NOTHING_TO_SEE_HERE\nMY_DUDE'})
print '##### RESPONSE STATUS CODE', response1.status_code
print '##### RESPONSE CONTENT', response1.content
# print '##### Rep1', dir(response1)
# print '##### Rep1', response1.text
# print '##### Rep1', dir(response1.raw)
# Test the image drawing route.
testGlmPath = omf.omfDir + '/scratch/GRIP/test_ieee123nodeBetter.glm'
response2 = requests.post('http://localhost:5100/oneLineGridlab', files={'glm':open(testGlmPath).read()}, data={'useLatLons':False})
# print response2.content # it's a png yo. don't actually print it. duh.
# Test the file conversion code.
testStdPath = omf.omfDir + '/static/testFiles/IEEE13.std'
testSeqPath = omf.omfDir + '/static/testFiles/IEEE13.seq'
response3 = requests.post('http://localhost:5100/milsoftToGridlab', files={'std':open(testStdPath).read(),'seq':open(testSeqPath).read()})
# print response3.content # it's a glm.
# Block until the process terminates.
mdbTestPath = omf.omfDir + '/static/testFiles/IEEE13.mdb'
response4 = requests.post('http://localhost:5100/cymeToGridlab', files={'mdb':open(mdbTestPath).read()})
# print response4.content # it's a glm.
response5 = requests.post(
	'http://localhost:5100/gridlabdToGfm',
	files = {'glm': open(testGlmPath).read()},
	data = {
		'phase_variation': '0.15',
		'chance_constraint': '1.0',
		'critical_load_met': '0.98',
		'total_load_met': '0.5',
		'maxDGPerGenerator': '0.5',
		'dgUnitCost': '1000000.0',
		'generatorCandidates': '',
		'criticalLoads': ''
	}
)
# print response5.content # it's a gfm model json.
response6 = requests.post('http://localhost:5100/gridlabRun', files={'glm':open(testGlmPath).read()})
# print response6.content # it's a big json.
response7 = requests.post(
	'http://localhost:5100/samRun',
	data = {
		'file_name': omf.omfDir + '/data/Climate/CA-SAN_FRANCISCO.tmy2',
		'system_size': 10.0,
		'derate': 0.77,
		'track_mode': 0.0,
		'azimuth': 180.0,
		'tilt_eq_lat': 1.0,
		'tilt': 45.0,
		'rotlim': 45.0,
		'gamma': -0.45,
		'inv_eff': 0.95,
		'w_stow': 100
	}
)
# print response7.content
response8 = requests.post(
	'http://localhost:5100/runGfm',
	files = {
		'gfm': response5.content,
		'asc': open(omf.omfDir + '/static/testFiles/wf_clip.asc').read()
	}
)
# print response8.content # it's a json.
# I SUFFER. KILL ME.
p.terminate()
# Or just join and serve forever. I don't care.
# p.join()
"""