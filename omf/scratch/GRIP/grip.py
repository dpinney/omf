''' Web server exposing HTTP API for GRIP. '''
import os, omf
if not omf.omfDir == os.getcwd():
	os.chdir(omf.omfDir)
import web, json
from gevent.pywsgi import WSGIServer
from flask import request

@web.app.route('/eatfile', methods=['GET', 'POST'])
def eatfile():
	if request.method == 'POST':
		print 'HEY I GOT A', request.files
		return 'POSTER_CHOMPED'
	else:
		return 'CHOMPED'

@web.app.route('/oneLineGridlab', methods=['GET', 'POST'])
def oneLineGridlab():
	'''Data Params: {glm: [file]}
	OMF fuction: omf.feeder.latLonNxGraph()
	Runtime: should be around 1 to 30 seconds.
	Result: Create a one line diagram of the circuit with :id in the datastore. Return a path to a folder in a filesystem where the .png was created.
	'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/milsoftToGridlab', methods=['GET', 'POST'])
def milsoftToGridlab():
	'''Data Params: {std: [file], seq: [file]}
	Runtime: could take a couple minutes.
	OMF function: omf.milToGridlab.convert()
	Result: a .glm file converted from the two input files.'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/cymeToGridlab', methods=['GET', 'POST'])
def cymeToGridlab():
	'''Data Params: {mdb: [file]}
	OMF function: omf.cymeToGridlab.convertCymeModel()
	Result: a .glm file converted from the input file.'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/gridlabRun', methods=['GET', 'POST'])
def gridlabRun():
	'''Data Params: {glm: [file]}
	Runtime: could take hours. Jeepers.
	OMF fuction: omf.solvers.gridlabd.runInFileSystem()
	Result: Run a GridLAB-D model and return the results as JSON.'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/samRun', methods=['GET', 'POST'])
def samRun():
	'''Data Params: {[system advisor model inputs, approximately 30 floats and strings]}
	OMF function: omf.solvers.sam.run()
	Runtime: should only be a couple seconds.
	Result: Run NREL's system advisor model with the specified parameters. Return the output vectors and floats in JSON'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/gridlabdToGfm', methods=['GET', 'POST'])
def gridlabdToGfm():
	'''Data Params: {glm: [file]}
	OMF function: omf.models.resilientDist.convertToGFM()
	Runtime: should only be a couple seconds.
	Result: Convert the GridLAB-D model to a GFM model. Return the new id for the converted model. Note that this is not the main fragility model for GRIP.'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/runGfm', methods=['GET', 'POST'])
def runGfm():
	'''Data Params: {gfm: [file]}
	OMF function: omf.solvers.gfm.run()
	Runtime: should be around 1 to 30 seconds.
	Result: Return the results dictionary/JSON from running LANL's General Fragility Model (GFM) on the input model. Note that this is not the main fragility model for GRIP.'''
	return 'NOT IMPLEMENTED YET'

def serve():
	server = WSGIServer(('0.0.0.0', 5000), web.app)
	server.serve_forever()

if __name__ == '__main__':
	serve()