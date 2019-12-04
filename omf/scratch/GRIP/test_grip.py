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
#from multiprocessing import Process
import io, os, omf, grip, requests, pytest, json
import omf

# Start the server.
#p = Process(target=grip.serve, args=())
#p.start()
# Shouldn't I join() here? Block the execution of the testing code until the server process finishes. Well, the server process never finishes.
# Can I send some kind of signal? I'll worry about that later. Just do something.

@pytest.fixture(scope="module") # The client should only be created once
def client():
    # testing must be set to true on the Flask application
    grip.app.config['TESTING'] = True
    # create a test client with built-in Flask code
    client = grip.app.test_client()
    # 'yield' instead of 'return' due to how fixtures work in pytest
    yield client
    # Could put teardown code here if needed

post_routes = [
    '/oneLineGridlab',
    '/milsoftToGridlab',
    '/cymeToGridlab',
    '/gridlabRun',
    '/gridlabdToGfm',
    '/runGfm',
    '/samRun',
    '/transmissionMatToOmt',
    '/transmissionPowerflow',
    '/transmissionViz',
    '/distributionViz'
]


@pytest.mark.parametrize('url_route', post_routes) # Apply this test to all routes
def test_GETRequestToPOSTRoute_returns405(url_route, client):
    response = client.get(url_route)
    assert response.status_code == 405


class Test_oneLineGridlab_start(object):

    def test_GLMHasNoCoordinates_and_useLatLonsIsTrue_returns422_and_returnsCorrectJSON(self, client):
        filename = 'test_ieee123nodeBetter.glm' 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            'glm': (b_io, filename),
            'useLatLons': 'True'
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 422
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 422,
                u'source': {u'useLatLons': u'True'},
                u'title': u'Invalid Parameter Value Combination',
                u'detail': (u"Since the submitted GLM contained no coordinates, 'useLatLons' must be 'False' because "
                    "artificial coordinates must be used to draw the GLM.")
            }]
        }

    def test_omittedUseLatLonsFormParameter_returns400_and_returnsCorrectJSON(self, client):
        filename = 'test_ieee123nodeBetter.glm' 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            'glm': (b_io, filename),
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'useLatLons': None},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'useLatLons' of type '<type 'bool'>' is required, but it was not submitted."
            }]
        }

    def test_omittedGLMFile_returns400_and_returnsCorrectJSON(self, client):
        data = {
            'glm': None,
            'useLatLons': True
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'glm': None},
                u'title': u'Invalid Parameter Value',
                u"detail": u"The parameter 'glm' of type 'file' is required, but it was not submitted."
            }]
        }

    def test_useLatLonsFormParameterIsTheStringtrue_returns400(self, client):
        filename = 'test_ieee123nodeBetter.glm' 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            'glm': (b_io, filename),
            'useLatLons': 'true'
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'useLatLons': u'true'},
                u'title': u'Invalid Parameter Value',
                u"detail": u"The parameter 'useLatLons' could not be converted into the required type '<type 'bool'>'."
            }]
        } 

    def test_useLatLonsFormParameterIsTheStringfalse_returns400(self, client):
        filename = 'test_ieee123nodeBetter.glm' 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            'glm': (b_io, filename),
            'useLatLons': 'false'
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'useLatLons': u'false'},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'useLatLons' could not be converted into the required type '<type 'bool'>'."
            }]
        } 


class Test_oneLineGridlab_status(object):
    pass


class Test_oneLineGridlab_download(object):

    def test_glmHasNoCoordinates_returnsCorrectPNG(self):
        filename = 'test_ieee123nodeBetter.glm' 
        test_file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(test_file_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            'glm': (b_io, filename),
            'useLatLons': False
        }
        response = client.post('/oneLineGridlab', data=data)
        #assert response.status_code == 200
        assert response.mimetype == 'image/png'
        assert response.content_length == 50394

    def test_glmHasCoordinates_returnsCorrectPNG(self):
        pass


class Test_milsoftToGridlab_start(object):

    def test_omittedSEQFile_returns400_and_returnsCorrectJSON(self, client):
        std_path = os.path.join(omf.omfDir, "static/testFiles/IEEE13.std")
        with open(std_path) as f:
            b_io_std = io.BytesIO(f.read())
        data = {"std": (b_io_std, "IEEE13.std")}
        response = client.post("/milsoftToGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'seq': None},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'seq' of type 'file' is required, but it was not submitted."
            }]
        }

    def test_omittedSTDFile_returns400_and_returnsCorrectJSON(self, client):
        seq_path = os.path.join(omf.omfDir, "static/testFiles/IEEE13.seq") 
        with open(seq_path) as f:
            b_io_seq = io.BytesIO(f.read())
        data = {"seq": (b_io_seq, "IEEE13.seq")}
        response = client.post("/milsoftToGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'std': None},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'std' of type 'file' is required, but it was not submitted."
            }]
        }


class Test_milsoftToGridlab_status(object):
    pass


class Test_milsoftToGridlab_download(object):
    pass


class TestCymeToGridlab(object):

    def test_omittedMDBFile_returns400_and_returnsCorrectJSON(self, client):
        #mdb_path = os.path.join(omf.omfDir, "static/testFiles/IEEE13.mdb")
        #with open(mdb_path) as f:
        #    b_io = io.BytesIO(f.read())
        #data = {"mdb": (b_io, "IEEE13.mdb")}
        data = {}
        response = client.post("/cymeToGridlab", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'mdb': None},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'mdb' of type 'file' is required, but it was not submitted."
            }]
        }


class TestGridlabRun(object):

    def test_omittedGLMFile_returns400_and_returnsCorrectJSON(self, client):
        data = {}
        response = client.post("/gridlabRun", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'glm': None},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'glm' of type 'file' is required, but it was not submitted."
            }]
        }

class TestGridlabdToGfm(object):

    def test_phaseVariationAboveMaxBound_returns400_and_returnsCorrectJSON(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, filename),
            "phase_variation": "1.01",
        }
        response = client.post("/gridlabdToGfm", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'phase_variation': 1.01},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'phase_variation' was greater than the maximum bound of '1'."
            }]
        }


class TestRunGfm(object):
    pass


class TestSamRun(object):
    
    def test_derateBelowMinBound_returns400_and_returnsCorrectJSON(self, client):
        tmy2_path = os.path.join(omf.omfDir, "data/Climate/CA-SAN_FRANCISCO.tmy2")
        with open(tmy2_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "tmy2": (b_io, "CA-SAN_FRANCISCO.tmy2"),
            "derate": -.01,
        }
        response = client.post("/samRun", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'derate': -0.01},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'derate' was less than the minimum bound of '0'."
            }]
        }


class TestTransmissionMatToOmt(object):
    pass


class TestTransmissionPowerflow(object):

    def test_algorithmNotInAllowedValues_returns400_and_returnsCorrectJSON(self, client):
        with open(os.path.join(omf.omfDir, "static/testFiles/case9.omt")) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "omt": (b_io, "case9.omt"),
            'algorithm': 'foobar'
        }
        response = client.post("/transmissionPowerflow", data=data)
        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data == {
            u'job': {
                u'state': u'failed'
            },
            u'errors': [{
                u'http code': 400,
                u'source': {u'algorithm': u'foobar'},
                u'title': u'Invalid Parameter Value',
                u'detail': u"The parameter 'algorithm' was not one of the allowed values: '('NR', 'FDXB', 'FDBX', 'GS')'."
            }]
        }


class TestTransmissionViz(object):
    pass


class TestDistributionViz(object):
    pass


# v1.0 tests
'''
@pytest.mark.parametrize("url_route", all_routes)
def test_postMissingFiles_returns400(url_route, client):
    response = client.post(url_route)
    assert response.status_code == 400

class TestOneLineGridlab(object):

    # Should return a 202
    def test_useLatLonsIsTrue_returnsSmallerPng(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            'glm': (b_io, filename),
            'useLatLons': True
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 200
        assert response.mimetype == "image/png"
        assert response.content_length == 2579

    # Should return a 202
    def test_useLatLonsIsFalse_returnsLargerPng(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        test_file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(test_file_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, filename),
            "useLatLons": False
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 200
        assert response.mimetype == "image/png"
        assert response.content_length == 50394

    def test_postWrongFileType_returns415(self, client):
        with open(__file__) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, "test_grip.py"),
        }
        response = client.post("/oneLineGridlab", data=data)
        assert response.status_code == 415
'''
'''
class TestMilsoftToGridlab(object):

    # Should return a 202
    def test_postRequest_returnsGlm(self, client):
        std_path = os.path.join(omf.omfDir, "static/testFiles/IEEE13.std")
        seq_path = os.path.join(omf.omfDir, "static/testFiles/IEEE13.seq") 
        with open(std_path) as f:
            b_io_std = io.BytesIO(f.read())
        with open(seq_path) as f:
            b_io_seq = io.BytesIO(f.read())
        data = {
            "std": (b_io_std, "IEEE13.std"),
            "seq": (b_io_seq, "IEEE13.seq"),
        }
        response = client.post("/milsoftToGridlab", data=data)
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert response.content_length >= 13650 and response.content_length <= 13750

    def test_postWrongFileType_returns415(self, client):
        std_path = __file__
        seq_path = __file__
        with open(std_path) as f:
            b_io_std = io.BytesIO(f.read())
        with open(seq_path) as f:
            b_io_seq = io.BytesIO(f.read())
        data = {
            "std": (b_io_std, "test_grip.py"),
            "seq": (b_io_seq, "test_grip.py"),
        }
        response = client.post("/milsoftToGridlab", data=data)
        assert response.status_code == 415

class TestCymeToGridlab(object):

    def test_postRequest_returnsGlm(self, client):
        mdb_path = os.path.join(omf.omfDir, "static/testFiles/IEEE13.mdb")
        with open(mdb_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "mdb": (b_io, "IEEE13.mdb"),
        }
        response = client.post("/cymeToGridlab", data=data)
        assert response.status_code == 200
        assert response.mimetype == "text/plain"
        assert response.content_length >= 25400 and response.content_length <= 25500

    def test_postWrongFileType_returns415(self, client):
        mdb_path = __file__
        with open(mdb_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "mdb": (b_io, "test_grip.py")
        }
        response = client.post("/cymeToGridlab", data=data)
        assert response.status_code == 415

class TestGridlabRun(object):

    # This test fails because the simulation seems to randomly succeed or fail
    def test_postRequest_returnsJSON(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, filename),
        }
        response = client.post("/gridlabRun", data=data)
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.content_length >= 1450 and response.content_length <= 1550 #1588 (successful simulation), 1535, 1453 (success), 641 (failed), 596 (failed)

    def test_postWrongFileType_returns415(self, client):
        glm_path = __file__
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, "test_grip.py"),
        }
        response = client.post("/gridlabRun", data=data)
        assert response.status_code == 415

class TestGridlabdToGfm(object):

    def test_postRequest_returnsJSON(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, filename),
            "phase_variation": "0.15",
            "chance_constraint": "1.0",
            "critical_load_met": "0.98",
            "total_load_met": "0.5",
            "maxDGPerGenerator": "0.5",
            "dgUnitCost": "1000000.0",
            "generatorCandidates": "",
            "criticalLoads": ""
        }
        response = client.post("/gridlabdToGfm", data=data)
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.content_length >= 37000 and response.content_length <= 38000 # 37228

    def test_postWrongFileType_returns415(self, client):
        with open(__file__) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, "test_grip.py"),
            "phase_variation": "0.15",
            "chance_constraint": "1.0",
            "critical_load_met": "0.98",
            "total_load_met": "0.5",
            "maxDGPerGenerator": "0.5",
            "dgUnitCost": "1000000.0",
            "generatorCandidates": "",
            "criticalLoads": ""
        }
        response = client.post("/gridlabdToGfm", data=data)
        assert response.status_code == 415

    def test_missingFormParameters_returns400(self, client):
        filename = "test_ieee123nodeBetter.glm" 
        glm_path = os.path.join(os.path.dirname(__file__), filename)
        with open(glm_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "glm": (b_io, filename),
        }
        response = client.post("/gridlabdToGfm", data=data)
        assert response.status_code == 400

# Don't touch this for now
class xTestRunGfm(object):

    def test_postRequest_returnsJSON(self, client):
        asc_path = os.path.join(omf.omfDir, "static/testFiles/wf_clip.asc")
        gfm_path = os.path.join(omf.omfDir, "static/testFiles/test_ieee123nodeBetter.gfm")
        with open(gfm_path) as f:
            b_io_gfm = io.BytesIO(f.read())
        with open(asc_path) as f:
            b_io_asc = io.BytesIO(f.read())
        data = {
            "gfm": (b_io_gfm, "test_ieee123nodeBetter.gfm"),
            "asc": (b_io_asc, "wf_clip.asc")
        }
        response = client.post("/runGfm", data=data)
        assert response.status_code == 200
        #assert response.mimetype == "application/json"
        #assert response.content_length >= 41300 and response.content_length <= 4140

    def test_postWrongFileType_returns415(self, client):
        asc_path = __file__
        gfm_path = __file__
        with open(gfm_path) as f:
            b_io_gfm = io.BytesIO(f.read())
        with open(asc_path) as f:
            b_io_asc = io.BytesIO(f.read())
        data = {
            "gfm": (b_io_gfm, "test_grip.py"),
            "asc": (b_io_asc, "test_grip.py")
        }
        response = client.post("/runGfm", data=data)
        # this is 200!?
        assert response.status_code == 415

# Don't touch this for now
class xTestSamRun(object):

    def test_postRequest_returnsJSON(self, client):
        tmy2_path = os.path.join(omf.omfDir, "data/Climate/CA-SAN_FRANCISCO.tmy2")
        with open(tmy2_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "file_name": (b_io, "CA-SAN_FRANCISCO.tmy2"),
            "system_size": 10.0,
            "derate": 0.77,
            "track_mode": 0.0,
            "azimuth": 180.0,
            "tilt_eq_lat": 1.0,
            "tilt": 45.0,
            "rotlim": 45.0,
            "gamma": -0.45,
            "inv_eff": 0.95,
            "w_stow": 100
        }
        response = client.post("/samRun", data=data)
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.content_length >= 300 and response.content_length <= 400

    def test_postWrongFileType_returns415(self, client):
        tmy2_path = __file__
        with open(tmy2_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "file_name": (b_io, "CA-SAN_FRANCISCO.tmy2"),
            "system_size": 10.0,
            "derate": 0.77,
            "track_mode": 0.0,
            "azimuth": 180.0,
            "tilt_eq_lat": 1.0,
            "tilt": 45.0,
            "rotlim": 45.0,
            "gamma": -0.45,
            "inv_eff": 0.95,
            "w_stow": 100
        }
        response = client.post("/samRun", data=data)
        # this is 200!?
        assert response.status_code == 415

class TestTransmissionMatToOmt(object):

    def test_postRequest_returnsJSON(self, client):
        mat_path = os.path.join(omf.omfDir, "solvers/matpower5.1", "case9.m")
        with open(mat_path) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "matpower": (b_io, "case9.m")
        }
        response = client.post("/transmissionMatToOmt", data=data)
        assert response.status_code == 200
        assert response.mimetype == "application/json"
        assert response.content_length >= 3700 and response.content_length <= 3800 # 3715

    # Must check if parse() result is equivalent to the default newNetworkWireframe because I don't know how to validate a .m file.
    def test_postWrongFileType_returns415(self, client):
        with open(__file__) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "matpower": (b_io, "test_grip.py")
        }
        response = client.post("/transmissionMatToOmt", data=data)
        assert response.status_code == 415

# Finish this, then create 202 strategy
class TestTransmissionPowerflow(object):
    pass

class TestTransmissionViz(object):
    
    def test_postRequest_returnsHTML(self, client):
        with open(os.path.join(omf.omfDir, "static/testFiles/case9.omt")) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "omt": (b_io, "case9.omt")
        }
        response = client.post("/transmissionViz", data=data)
        assert response.status_code == 200
        assert response.mimetype == "text/html"
        assert response.content_length >= 406500 and response.content_length <= 407500 #406949

    def test_postWrongFileType_returns415(self, client):
        with open(__file__) as f:
            b_io = io.BytesIO(f.read())
        data = {
            "omt": (b_io, "test_grip.py")
        }
        response = client.post("/transmissionViz", data=data)
        assert response.status_code == 415
'''



# Make sure it's up.
# webbrowser.open_new('http://localhost:5100/eatfile')
# Test a simple route.
#response1 = requests.post('http://localhost:5100/eatfile', files={'test.txt':'NOTHING_TO_SEE_HERE\nMY_DUDE'})
#print '##### RESPONSE STATUS CODE', response1.status_code
#print '##### RESPONSE CONTENT', response1.content
# print '##### Rep1', dir(response1)
# print '##### Rep1', response1.text
# print '##### Rep1', dir(response1.raw)
# Test the image drawing route.
#testGlmPath = omf.omfDir + '/scratch/GRIP/test_ieee123nodeBetter.glm'
#response2 = requests.post('http://localhost:5100/oneLineGridlab', files={'glm':open(testGlmPath).read()}, data={'useLatLons':False})
# print response2.content # it's a png yo. don't actually print it. duh.
# Test the file conversion code.
#testStdPath = omf.omfDir + '/static/testFiles/IEEE13.std'
#testSeqPath = omf.omfDir + '/static/testFiles/IEEE13.seq'
#response3 = requests.post('http://localhost:5100/milsoftToGridlab', files={'std':open(testStdPath).read(),'seq':open(testSeqPath).read()})
# print response3.content # it's a glm.
# Block until the process terminates.
#mdbTestPath = omf.omfDir + '/static/testFiles/IEEE13.mdb'
#response4 = requests.post('http://localhost:5100/cymeToGridlab', files={'mdb':open(mdbTestPath).read()})
# print response4.content # it's a glm.
#response5 = requests.post(
#	'http://localhost:5100/gridlabdToGfm',
#	files = {'glm': open(testGlmPath).read()},
#	data = {
#		'phase_variation': '0.15',
#		'chance_constraint': '1.0',
#		'critical_load_met': '0.98',
#		'total_load_met': '0.5',
#		'maxDGPerGenerator': '0.5',
#		'dgUnitCost': '1000000.0',
#		'generatorCandidates': '',
#		'criticalLoads': ''
#	}
#)
# print response5.content # it's a gfm model json.
#response6 = requests.post('http://localhost:5100/gridlabRun', files={'glm':open(testGlmPath).read()})
# print response6.content # it's a big json.

#response7 = requests.post(
#	'http://localhost:5100/samRun',
#	data = {
#		'file_name': omf.omfDir + '/data/Climate/CA-SAN_FRANCISCO.tmy2',
#		'system_size': 10.0,
#		'derate': 0.77,
#		'track_mode': 0.0,
#		'azimuth': 180.0,
#		'tilt_eq_lat': 1.0,
#		'tilt': 45.0,
#		'rotlim': 45.0,
#		'gamma': -0.45,
#		'inv_eff': 0.95,
#		'w_stow': 100
#	}
#)
# print response7.content

#response8 = requests.post(
#	'http://localhost:5100/runGfm',
#	files = {
#		'gfm': response5.content,
#		'asc': open(omf.omfDir + '/static/testFiles/wf_clip.asc').read()
#	}
#)
# print response8.content # it's a json.
# I SUFFER. KILL ME.
#p.terminate()
# Or just join and serve forever. I don't care.
# p.join()