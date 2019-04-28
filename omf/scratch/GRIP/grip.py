''' Web server exposing HTTP API for GRIP. '''
import omf
#if not omf.omfDir == os.getcwd():
#	os.chdir(omf.omfDir)
import tempfile, platform, subprocess, os, zipfile
from gevent.pywsgi import WSGIServer
from flask import Flask, request, send_from_directory, make_response, json, abort
import matplotlib.pyplot as plt

# TODO: note how I commented out the directory change, but it still appears to work (at least on my machine)

app = Flask(__name__)

@app.route('/oneLineGridlab', methods=['POST'])
def oneLineGridLab():
	''' Data Params: {glm: [file], useLatLons: Boolean}
	OMF fuction: omf.feeder.latLonNxGraph()
	Runtime: should be around 1 to 30 seconds.
    Result: Create a one line diagram of the input glm. Return a .png of it. If useLatLons is True then draw using the lat/lons, otherwise force
    layout the graph.
    '''
	temp_dir = tempfile.mkdtemp() 
	print temp_dir
	f = request.files['glm']
	glm_file_path = os.path.join(temp_dir, "in.glm")
	f.save(glm_file_path)
	try:
		feed = omf.feeder.parse(glm_file_path)
		graph = omf.feeder.treeToNxGraph(feed)
		if request.form.get('useLatLons') == 'False':
			neatoLayout = True
		else:
			neatoLayout = False
		# Clear old plots.
		plt.clf()
		plt.close()
		# Plot new plot.
		omf.feeder.latLonNxGraph(graph, labels=False, neatoLayout=neatoLayout, showPlot=False)
		out_img_name = 'out.png'
		plt.savefig(os.path.join(temp_dir, out_img_name))
		return send_from_directory(temp_dir, out_img_name)
	except:
		return ("", 415, {})

@app.route('/milsoftToGridlab', methods=['POST'])
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
	try:
		with open(stdPath) as f: stdFile = f.read()
		with open(seqPath) as f: seqFile = f.read()
		tree = omf.milToGridlab.convert(stdFile, seqFile, rescale=True)
		glmName = 'out.glm'
		glmPath = os.path.join(workDir, glmName)
		with open(glmPath, 'w') as outFile: outFile.write(omf.feeder.sortedWrite(tree))
		return send_from_directory(workDir, glmName, mimetype="text/plain")
	except:
		return ("", 415, {})

@app.route('/cymeToGridlab', methods=['POST'])
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
	try:
		tree = omf.cymeToGridlab.convertCymeModel(mdbPath, workDir)
		glmName = 'out.glm'
		glmPath = os.path.join(workDir, glmName)
		with open(glmPath, 'w') as outFile:
			outFile.write(omf.feeder.sortedWrite(tree))
		return send_from_directory(workDir, glmName, mimetype="text/plain")
	except:
		return ("", 415, {})

@app.route('/gridlabRun', methods=['POST'])
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
	try:
		feed = omf.feeder.parse(glmOnDisk)
		outDict = omf.solvers.gridlabd.runInFilesystem(feed, attachments=[], keepFiles=True, workDir=workDir, glmName='out.glm')
		return json.jsonify(outDict)
	except:
		return ("", 415, {})

@app.route('/gridlabdToGfm', methods=['POST'])
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
	try:
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
		for key, val in gfmInputTemplate.items():
			if val is None:
				return ("", 400, {})
	except:
		return ("", 400, {})
	try:
		feederModel = {
			'nodes': [], # Don't need these.
			'tree': omf.feeder.parse(glmPath)
		}
		gfmDict = omf.models.resilientDist.convertToGFM(gfmInputTemplate, feederModel)
		return json.jsonify(gfmDict)
	except:
		return ("", 415, {})

# Don't touch this for now
@app.route('/runGfm', methods=['POST'])
def runGfm():
	'''Data Params: {gfm: [file], asc: [file]}
	OMF function: omf.solvers.gfm.run()
	Runtime: should be around 1 to 30 seconds.
	Result: Return the results dictionary/JSON from running LANL's General Fragility Model (GFM) on the input model and .asc hazard field. Note that this is not the main fragility model for GRIP.'''
	workDir = tempfile.mkdtemp()
	fName = 'gfm.json'
	gfmPath = os.path.join(workDir, fName)
	f = request.files['gfm']
	f.save(gfmPath)
	hName = 'hazard.asc'
	hazardPath = os.path.join(workDir, hName)
	h = request.files['asc']
	h.save(hazardPath)
	# Run GFM
	gfmBinaryPath = os.path.join(omf.omfDir, "solvers/gfm/Fragility.jar")
	if platform.system() == 'Darwin':
		#HACK: force use of Java8 on MacOS.
		#javaCmd = '/Library/Java/JavaVirtualMachines/jdk1.8.0_181.jdk/Contents/Home/bin/java'
		#HACK HACK: use my version of Java 8 for now
		javaCmd = "/Library/Java/JavaVirtualMachines/jdk1.8.0_202.jdk/Contents/Home/bin/java"
	else:
		javaCmd = 'java'
	outName = 'gfm_out.json'
	proc = subprocess.Popen(
		[javaCmd,'-jar', gfmBinaryPath, '-r', fName, '-wf', hName, '-num', '3', '-ro', outName],
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE,
		cwd = workDir
	)
	(stdout,stderr) = proc.communicate()
	gfmOutPath = os.path.join(workDir, outName)
	try:
		out = json.load(open(gfmOutPath))
	except:
		out = stdout
	return out

@app.route('/samRun', methods=['POST'])
def samRun():
	'''Data Params: {[system advisor model inputs, approximately 30 floats]}
	OMF function: omf.solvers.sam.run()
	Runtime: should only be a couple seconds.
	Result: Run NREL's system advisor model with the specified parameters. Return the output vectors and floats in JSON'''
	temp_dir = tempfile.mkdtemp()
	tmy2_path = os.path.join(temp_dir, "in.tmy2")
	request.files["tmy2"].save(tmy2_path)
	# Set up SAM data structures.
	ssc = omf.solvers.nrelsam2013.SSCAPI()
	dat = ssc.ssc_data_create()
	# Set the inputs.
	ssc.ssc_data_set_string(dat, "file_name", tmy2_path)
	for key in request.form.keys():
		ssc.ssc_data_set_number(dat, key, float(request.form.get(key)))
	# Run PV system simulation.
	mod = ssc.ssc_module_create("pvwattsv1")
	ssc.ssc_module_exec(mod, dat)
	# Geodata output.
	outData = {}
	outData["city"] = ssc.ssc_data_get_string(dat, "city")
	outData["state"] = ssc.ssc_data_get_string(dat, "state")
	outData["lat"] = ssc.ssc_data_get_number(dat, "lat")
	outData["lon"] = ssc.ssc_data_get_number(dat, "lon")
	outData["elev"] = ssc.ssc_data_get_number(dat, "elev")
	# Weather output.
	outData["climate"] = {}
	outData["climate"]["Plane of Array Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "poa")
	outData["climate"]["Beam Normal Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "dn")
	outData["climate"]["Diffuse Irradiance (W/m^2)"] = ssc.ssc_data_get_array(dat, "df")
	outData["climate"]["Ambient Temperature (F)"] = ssc.ssc_data_get_array(dat, "tamb")
	outData["climate"]["Cell Temperature (F)"] = ssc.ssc_data_get_array(dat, "tcell")
	outData["climate"]["Wind Speed (m/s)"] = ssc.ssc_data_get_array(dat, "wspd")
	# Power generation.
	outData["Consumption"] = {}
	outData["Consumption"]["Power"] = ssc.ssc_data_get_array(dat, "ac")
	outData["Consumption"]["Losses"] = ssc.ssc_data_get_array(dat, "ac")
	outData["Consumption"]["DG"] = ssc.ssc_data_get_array(dat, "ac")
	return json.jsonify(outData)

@app.route('/transmissionMatToOmt', methods=['POST'])
def transmissionMatToOmt():
	'''Data Params: {mat: [file], other_inputs: see source}
	OMF function: omf.network.parse()
	Runtime: maybe a couple minutes.
	Result: Convert the .m matpower model to an OMT (JSON-based) model. Return the model.'''
	temp_dir = tempfile.mkdtemp() 
	mat_path = os.path.join(temp_dir, "input.m")
	request.files["matpower"].save(mat_path)
	omt_json = omf.network.parse(mat_path, filePath=True)
	if omt_json == {"baseMVA":"100.0","mpcVersion":"2.0","bus":{},"gen":{}, "branch":{}}:
		raise Exception("The submitted .m file was invalid or could not be parsed correctly.")
	nxG = omf.network.netToNxGraph(omt_json)
	omt_json = omf.network.latlonToNet(nxG, omt_json)
	return json.jsonify(omt_json)

@app.route('/transmissionPowerflow', methods=['POST'])
def transmissionPowerflow():
	'''Data Params: {omt: [file], other_inputs: see source}
	OMF function: omf.models.transmission.new and omf.models.transmission.work
	Runtime: tens of seconds.
	Result: TBD. '''
	try:
		try:
			tolerance = float(request.form.get("tolerance"))
		except:
			tolerance = None
		try:
			iteration = int(request.form.get("iteration"))
		except:
			iteration = None
		try: 
			genLimits = int(request.form.get("genLimits"))
		except:
			genLimits = None
		inputDict = {
			"user": request.form.get("user") if request.form.get("user") != "" else None,
			"networkName1": request.form.get("networkName1") if request.form.get("networkName1") != "" else None,
			"algorithm": request.form.get("algorithm") if request.form.get("algorithm") != "" else None,
			"model": request.form.get("model") if request.form.get("model") != "" else None,
			"tolerance": tolerance,
			"iteration": iteration,
			"genLimits": genLimits
			#"modelType": request.form.get("modelType")
		}
		temp_dir = tempfile.mkdtemp()
		model_dir = os.path.join(temp_dir, "transmission")
		if omf.models.transmission.new(model_dir):
			omt_path = os.path.join(model_dir, "case9.omt")
			request.files["omt"].save(omt_path)
			with open(os.path.join(model_dir, "allInputData.json")) as f:
				defaults = json.load(f)
			merged = {key: inputDict.get(key) if inputDict.get(key) is not None else defaults[key] for key in defaults}
			with open(os.path.join(model_dir, "allInputData.json"), 'w') as f:
				json.dump(merged, f)
			outputDict = omf.models.transmission.work(model_dir, merged)
			with open(os.path.join(model_dir, "allOutputData.json"), 'w') as f:
				json.dump(outputDict, f)
			with zipfile.ZipFile(os.path.join(model_dir, "transmission-powerflow.zip"), 'w', zipfile.ZIP_DEFLATED) as z:
				z.write(os.path.join(model_dir, "output.png"), "output.png")
				z.write(os.path.join(model_dir, "allOutputData.json"), "allOutputData.json")
			return send_from_directory(model_dir, "transmission-powerflow.zip", as_attachment=True)
		else:
			return("Couldn't create model directory", 400, {})
	except:
		abort(400)


@app.route('/transmissionViz', methods=['POST'])
def transmissionViz():
	'''Data Params: {omt: [file], other_inputs: see source}
	OMF function: omf.network.viz()
	Runtime: a couple seconds.
	Result: HTML interface visualizing the .omt file. '''
	f = request.files["omt"]
	temp_dir = tempfile.mkdtemp()
	omt_path = os.path.join(temp_dir, "in.omt")
	f.save(omt_path)
	try:
		with open(omt_path) as f:
			json.load(f)
	except:
		return ("", 415, {})
	html_filename = omf.network.get_HTML_interface_path(omt_path)
	return send_from_directory(temp_dir, html_filename)

def serve():
	server = WSGIServer(('0.0.0.0', 5100), app)
	server.serve_forever()

if __name__ == '__main__':
	serve()