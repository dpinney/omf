'''Test grip.py with pytest'''


import io, os, json, tempfile
from pathlib import Path
import requests
import pytest
from flask import url_for, request
import omf
from omf import feeder
from omf.solvers import gridlabd
from omf.scratch.GRIP import grip


# Place to hack on stuff. Not intended to be run with real tests via pytest
if __name__ == '__main__':
	temp_dir = tempfile.mkdtemp()
	path = Path(omf.omfDir) / 'scratch/CIGAR/test_ieee123nodeBetter.glm'
	#path = Path(__file__).parent / 'test-files/ieee123_pole_vulnerability.glm'
	feed = feeder.parse(path)
	#import pdb; pdb.set_trace()
	outDict = gridlabd.runInFilesystem(feed, attachments=[], keepFiles=True, workDir=temp_dir, glmName='out.glm')
	print(outDict)


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
	'/distributionViz',
	'/glmForceLayout'
]


@pytest.mark.parametrize('url_route', post_routes) # Apply this test to all routes
def test_GETRequestToPOSTRoute_returns405(url_route, client):
	response = client.get(url_route)
	assert response.status_code == 405


class Test_validateInput:
	'''
	Normally I don't want to test a private method but this is a rare exception
	- All of these tests must operate within a requests context
	'''

	def test_validMetadataInputType_returnsCorrectTuple(self):
		request_data = {'my_input': 4}
		with grip.app.test_request_context(data=request_data):
			input_metadata = {
				'name': 'my_input',
				'required': True,
				'type': float
			}
			t = grip._validate_input(input_metadata)
		assert t == (None, None)

	def test_emptyFormFileInput_returnsCorrectTuple(self):
		request_data = {
			'my_file': (io.BytesIO(), '') # Simulate sending HTML file input that hasn't had a file selected
		}
		with grip.app.test_request_context(data=request_data):
			input_metadata = {
				'name': 'my_file',
				'required': True,
				'type': 'file'
			}
			t = grip._validate_input(input_metadata)
		assert t == ({'my_file': None}, "The parameter 'my_file' of type 'file' is required, but it was not submitted.")

	def test_nonexistentFormFileInput_returnsCorrectTuple(self):
		# We need to check for if a file form parameter was not submitted at all
		request_data = {}
		with grip.app.test_request_context(data=request_data):
			input_metadata = {
				'name': 'my_file',
				'required': True,
				'type': 'file'
			}
			t = grip._validate_input(input_metadata)
		assert t == ({'my_file': None}, "The parameter 'my_file' of type 'file' is required, but it was not submitted.")

	def test_nonexistentMetadataInputType_returnsCorrectTuple(self):
		# There is no such thing as a 'foobar' type. This test is to catch any programmer error where the 'type' attribute is set to anything that
		# isn't a real Python type
		request_data = {'my_input': 'blah'}
		with grip.app.test_request_context(data=request_data):
			input_metadata = {
				'name': 'my_input',
				'required': True,
				'type': 'foobar'
			}
			t = grip._validate_input(input_metadata)
		assert t == ({'my_input': 'blah'}, "The parameter 'my_input' could not be converted into the required type 'foobar'.")

	def test_invalidMetadataInputType_returnsCorrectTuple(self):
		# This will catch when the user submits something that is supposed to be castable to a int, but isn't
		request_data = {'my_input': '?'}
		with grip.app.test_request_context(data=request_data):
			input_metadata = {
				'name': 'my_input',
				'required': True,
				'type': int
			}
			t = grip._validate_input(input_metadata)
		assert t == ({'my_input': '?'}, "The parameter 'my_input' could not be converted into the required type '<class 'int'>'.")


class Test_oneLineGridlab_start:

	def test_GLMHasNoCoordinates_and_useLatLonsIsTrue_returns422_and_returnsCorrectJSON(self, client):
		glm_path = Path(omf.omfDir) / 'scratch/CIGAR/test_ieee123nodeBetter.glm'
		with open(glm_path, 'rb') as f:
			b_io = io.BytesIO(f.read())
		data = {
			'glm': (b_io, 'filename'),
			'useLatLons': 'True'
		}
		response = client.post("/oneLineGridlab", data=data)
		assert response.status_code == 422
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 422,
				'source': {'useLatLons': 'True'},
				'title': 'Invalid Parameter Value Combination',
				'detail': ("Since the submitted GLM contained no coordinates, or the coordinates could not be parsed as floats, "
					"'useLatLons' must be 'False' because artificial coordinates must be used to draw the GLM.")
			}]
		}

	def test_GLMHasInvalidCoordinates_and_useLatLonsIsTrue_returns422_and_returnsCorrectJSON(self, client):
		glm_path = Path(__file__).parent / 'test-files/ieee123_pole_vulnerability.glm'
		with open(glm_path, 'rb') as f:
			b_io = io.BytesIO(f.read())
		data = {
			'glm': (b_io, 'filename'),
			'useLatLons': 'True'
		}
		response = client.post("/oneLineGridlab", data=data)
		assert response.status_code == 422
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 422,
				'source': {'useLatLons': 'True'},
				'title': 'Invalid Parameter Value Combination',
				'detail': ("Since the submitted GLM contained no coordinates, or the coordinates could not be parsed as floats, "
					"'useLatLons' must be 'False' because artificial coordinates must be used to draw the GLM.")
			}]
		}

	def test_omittedUseLatLonsFormParameter_returns400_and_returnsCorrectJSON(self, client):
		data = {'glm': (io.BytesIO(), 'filename')}
		response = client.post("/oneLineGridlab", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'useLatLons': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'useLatLons' of type '<class 'bool'>' is required, but it was not submitted."
			}]
		}

	def test_omittedGLMFile_returns400_and_returnsCorrectJSON(self, client):
		data = {'useLatLons': 'True'}
		response = client.post("/oneLineGridlab", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'glm': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'glm' of type 'file' is required, but it was not submitted."
			}]
		}

	@pytest.mark.parametrize('useLatLons', ('true', 'false', 5, None))
	def test_useLatLonsFormParameterIsNotTheStringTrueNorFalse_returns400(self, client, useLatLons):
		data = {
			'glm': (io.BytesIO(), 'filename'),
			'useLatLons': useLatLons
		}
		response = client.post("/oneLineGridlab", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'useLatLons': str(useLatLons)},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'useLatLons' could not be converted into the required type '<class 'bool'>'."
			}]
		} 


class Test_oneLineGridlab_status:
	pass


class xTest_oneLineGridlab_download:
	pass

	def test_glmHasNoCoordinates_returnsCorrectPNG(self, client):
		'''
		TODO: Two approaches:
		1) Spy on mkdtemp(). Send a GET request to onelineGridlab as normal. Instead of polling, send the GET request to onelineGridlab_download when
		   I detect the temp_dir has the desired arguments. This isn't any better than the second approach, and is in fact just a worse integration
		   test.
			- If this were a real unit test of onelineGridlab_download itself, I would just be creating a fake file in the temp_dir and making sure that
			  onelineGridlab_download would return it. Since the logic of onelineGridlab_download is so simple, it doesn't make sense to unit test this
		2) POST to /onlineGridlab as normal. Get the response JSON (This is an integration test, which isn't a bad thing). 
			- Poll the status URL until I get the download URL, then GET the download URL and inspect the contents
			- Can't use asyncio because the status page returns immediately. Or can I? Can I conditionally advance an asyncIO web request? Say,
			  advance if the resposne wasn't 404? But the point of asycIO is to only wait for the web request to return, so I don't think I can do
			  this. All this would do (if it were possible) is push the polling logic into asycIO itself
		'''
		test_file_path = Path(omf.omfDir) / 'scratch/CIGAR/test_ieee123nodeBetter.glm'
		with open(test_file_path) as f:
			b_io = io.BytesIO(bytes(f.read(), 'ascii'))
		data = {
			'glm': (b_io, filename),
			'useLatLons': False
		}
		response = client.get(url_for("oneLineGridlab_download", temp_dir=temp_dir))
		#response = client.post('/oneLineGridlab', data=data)
		#assert response.status_code == 200
		assert response.mimetype == 'image/png'
		assert response.content_length == 50394

	#def test_glmHasCoordinates_returnsCorrectPNG(self):
	#	 pass


class Test_milsoftToGridlab_start:

	def test_omittedSEQFile_returns400_and_returnsCorrectJSON(self, client):
		data = {
			'std': (io.BytesIO(), 'filename')
		}
		response = client.post('/milsoftToGridlab', data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'seq': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'seq' of type 'file' is required, but it was not submitted."
			}]
		}

	def test_omittedSTDFile_returns400_and_returnsCorrectJSON(self, client):
		data = {'seq': (io.BytesIO(), 'filename')}
		response = client.post('/milsoftToGridlab', data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'std': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'std' of type 'file' is required, but it was not submitted."
			}]
		}


class Test_milsoftToGridlab_status:
	pass


class Test_milsoftToGridlab_download:
	pass


class Test_cymeToGridlab_start:

	def test_omittedMDBFile_returns400_and_returnsCorrectJSON(self, client):
		data = {}
		response = client.post("/cymeToGridlab", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'mdb': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'mdb' of type 'file' is required, but it was not submitted."
			}]
		}


class Test_cymeToGridlab_status:
	pass


class Test_cymeToGridlab_download:
	pass


class Test_gridlabRun_start:

	def test_omittedGLMFile_returns400_and_returnsCorrectJSON(self, client):
		data = {}
		response = client.post("/gridlabRun", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'glm': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'glm' of type 'file' is required, but it was not submitted."
			}]
		}

class Test_gridlabRun_status:
	pass


class Test_gridlabRun_download:
	pass


class Test_gridlabdToGfm_start:

	def test_phaseVariationAboveMaxBound_returns400_and_returnsCorrectJSON(self, client):
		data = {
			"glm": (io.BytesIO(), 'filename'),
			"phase_variation": "1.01"
		}
		response = client.post("/gridlabdToGfm", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'phase_variation': 1.01},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'phase_variation' was greater than the maximum bound of '1'."
			}]
		}


class Test_gridlabdToGfm_status():
	pass


class Test_gridlabdToGfm_download():
	pass


class Test_runGfm_start:
	pass


class Test_runGfm_status:
	pass


class Test_runGfm_download:
	pass


class Test_samRun_start:
	
	def test_derateBelowMinBound_returns400_and_returnsCorrectJSON(self, client):
		data = {
			'tmy2': (io.BytesIO(), 'filename'),
			'derate': -.01,
		}
		response = client.post("/samRun", data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'derate': -0.01},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'derate' was less than the minimum bound of '0'."
			}]
		}

class Test_samRun_status:
	pass


class Test_samRun_download:
	pass


class Test_transmissionMatToOmt_start:
	pass


class Test_transmissionMatToOmt_status:
	pass


class Test_transmissionMatToOmt_download:
	pass


class Test_transmissionPowerflow_start:

	def test_algorithmNotInAllowedValues_returns400_and_returnsCorrectJSON(self, client):
		data = {
			'omt': (io.BytesIO(), 'filename'),
			'algorithm': 'foobar'
		}
		response = client.post('/transmissionPowerflow', data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'algorithm': 'foobar'},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'algorithm' was not one of the allowed values: '('NR', 'FDXB', 'FDBX', 'GS')'."
			}]
		}


class Test_transmissionPowerflow_status:
	pass


class Test_transmissionPowerflow_download:
	pass


class Test_transmissionViz_start:
	pass


class Test_transmissionViz_status:
	pass


class Test_transmissionViz_download:
	pass


class Test_distributionViz_start:
	pass


class Test_distributionViz_status:
	pass


class Test_distributionViz_download:
	pass


class Test_glmForceLayout_start:

	def test_omittedGLMFile_returns400_and_returnsCorrectJSON(self, client):
		data = {}
		response = client.post('/glmForceLayout', data=data)
		assert response.status_code == 400
		response_data = json.loads(response.data)
		assert response_data == {
			'job': {
				'state': 'failed'
			},
			'errors': [{
				'http code': 400,
				'source': {'glm': None},
				'title': 'Invalid Parameter Value',
				'detail': "The parameter 'glm' of type 'file' is required, but it was not submitted."
			}]
		}


class Test_glmForceLayout_status:
	pass


class Test_glmForceLayout_download:
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
		mat_path = os.path.join(omf.omfDir, "solvers/matpower7.0", "data, "case9.m")
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
