''' Web server exposing HTTP API for GRIP. '''
import os, omf
if not omf.omfDir == os.getcwd():
	os.chdir(omf.omfDir)
import web, json, tempfile
from gevent.pywsgi import WSGIServer
from flask import request, send_from_directory
from matplotlib import pyplot as plt

@web.app.route('/eatfile', methods=['GET', 'POST'])
def eatfile():
	if request.method == 'POST':
		# print 'HEY I GOT A', request.files
		return 'POSTER_CHOMPED'
	else:
		return 'CHOMPED'

@web.app.route('/oneLineGridlab', methods=['POST'])
def oneLineGridlab():
	'''Data Params: {glm: [file], useLatLons: Boolean}
	OMF fuction: omf.feeder.latLonNxGraph()
	Runtime: should be around 1 to 30 seconds.
	Result: Create a one line diagram of the input glm. Return a .png of it. If useLatLons is True then draw using the lat/lons, otherwise force layout the graph.'''
	workDir = tempfile.mkdtemp()
	fName = 'in.glm'
	f = request.files['glm']
	glmOnDisk = os.path.join(workDir, fName)
	f.save(glmOnDisk)
	feed = omf.feeder.parse(glmOnDisk)
	graph = omf.feeder.treeToNxGraph(feed)
	if request.form.get('useLatLons') == 'False':
		neatoLayout = True
	else:
		neatoLayout = False
	matplotObj = omf.feeder.latLonNxGraph(graph, labels=False, neatoLayout=neatoLayout, showPlot=False)
	outImgName = 'out.png'
	outImgPath = os.path.join(workDir, outImgName)
	plt.savefig(outImgPath)
	# TODO: delete the tempDir.
	return send_from_directory(workDir, outImgName)

@web.app.route('/milsoftToGridlab', methods=['POST'])
def milsoftToGridlab():
	'''Data Params: {std: [file], seq: [file]}
	Runtime: could take a couple minutes.
	OMF function: omf.milToGridlab.convert()
	Result: a .glm file converted from the two input files.'''
	workDir = tempfile.mkdtemp()
	stdFileName = 'in.std'
	stdFile = request.files['std']
	stdPath = os.path.join(workDir, stdFileName)
	stdFile.save(stdPath)
	seqFileName = 'in.seq'
	seqFile = request.files['seq']
	seqPath = os.path.join(workDir, seqFileName)
	seqFile.save(seqPath)
	tree = omf.milToGridlab.convert(open(stdPath).read(), open(seqPath).read(), rescale=True)
	glmName = 'out.glm'
	glmPath = os.path.join(workDir, glmName)
	with open(glmPath, 'w') as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))
	# TODO: delete the tempDir.
	return send_from_directory(workDir, glmName)

@web.app.route('/cymeToGridlab', methods=['POST'])
def cymeToGridlab():
	'''Data Params: {mdb: [file]}
	OMF function: omf.cymeToGridlab.convertCymeModel()
	Result: a .glm file converted from the input file.'''
	workDir = tempfile.mkdtemp()
	mdbFileName = 'in.mdb'
	mdbFile = request.files['mdb']
	mdbPath = os.path.join(workDir, mdbFileName)
	mdbFile.save(mdbPath)
	import locale
	locale.setlocale(locale.LC_ALL, 'en_US')
	tree = omf.cymeToGridlab.convertCymeModel(mdbPath, workDir)
	glmName = 'out.glm'
	glmPath = os.path.join(workDir, glmName)
	with open(glmPath, 'w') as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))
	# TODO: delete the tempDir.
	return send_from_directory(workDir, glmName)

@web.app.route('/gridlabRun', methods=['POST'])
def gridlabRun():
	'''Data Params: {glm: [file]}
	Runtime: could take hours. Jeepers.
	OMF fuction: omf.solvers.gridlabd.runInFileSystem()
	Result: Run a GridLAB-D model and return the results as JSON.
	TODO: think about attachment support.'''
	workDir = tempfile.mkdtemp()
	fName = 'in.glm'
	f = request.files['glm']
	glmOnDisk = os.path.join(workDir, fName)
	f.save(glmOnDisk)
	feed = omf.feeder.parse(glmOnDisk)
	outDict = omf.solvers.gridlabd.runInFilesystem(feed, attachments=[], keepFiles=True, workDir=workDir, glmName='out.glm')
	#TODO: delete the tempDir.
	return json.dumps(outDict)

@web.app.route('/gridlabdToGfm', methods=['POST'])
def gridlabdToGfm():
	'''Data Params: {glm: [file], other_inputs: see source}
	OMF function: omf.models.resilientDist.convertToGFM()
	Runtime: should only be a couple seconds.
	Result: Convert the GridLAB-D model to a GFM model. Return the new id for the converted model. Note that this is not the main fragility model for GRIP.'''
	workDir = tempfile.mkdtemp()
	fName = 'in.glm'
	f = request.files['glm']
	glmPath = os.path.join(workDir, fName)
	f.save(glmPath)
	feederModel = {
		'nodes': [], # Don't need these.
		'tree': omf.feeder.parse(glmPath)
	}
	gfmInputTemplate = {
		'phase_variation': float(request.form.get('phase_variation')),
		'chance_constraint': float(request.form.get('chance_constraint')),
		'critical_load_met': float(request.form.get('critical_load_met')),
		'total_load_met': float(request.form.get('total_load_met')),
		'maxDGPerGenerator': float(request.form.get('maxDGPerGenerator')),
		'dgUnitCost': float(request.form.get('dgUnitCost')),
		'generatorCandidates': request.form.get('generatorCandidates'),
		'criticalLoads': request.form.get('criticalLoads')
	}
	gfmDict = omf.models.resilientDist.convertToGFM(gfmInputTemplate, feederModel)
	# TODO: delete the tempDir.
	return json.dumps(gfmDict)

@web.app.route('/runGfm', methods=['GET', 'POST'])
def runGfm():
	'''Data Params: {gfm: [file]}
	OMF function: omf.solvers.gfm.run()
	Runtime: should be around 1 to 30 seconds.
	Result: Return the results dictionary/JSON from running LANL's General Fragility Model (GFM) on the input model. Note that this is not the main fragility model for GRIP.'''
	return 'NOT IMPLEMENTED YET'

@web.app.route('/samRun', methods=['GET', 'POST'])
def samRun():
	'''Data Params: {[system advisor model inputs, approximately 30 floats and strings]}
	OMF function: omf.solvers.sam.run()
	Runtime: should only be a couple seconds.
	Result: Run NREL's system advisor model with the specified parameters. Return the output vectors and floats in JSON'''
	return 'NOT IMPLEMENTED YET'

def serve():
	server = WSGIServer(('0.0.0.0', 5000), web.app)
	server.serve_forever()

if __name__ == '__main__':
	serve()