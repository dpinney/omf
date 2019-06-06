''' Web server exposing HTTP API for GRIP. '''
import omf
import os
# TODO: note how I commented out the directory change, but it still appears to work (at least on my machine)
#if not omf.omfDir == os.getcwd():
	#os.chdir(omf.omfDir)
import tempfile, platform, subprocess, zipfile, subprocess, time, shutil, sys, threading
from functools import wraps
from multiprocessing import Process
import matplotlib.pyplot as plt
from flask import Flask, request, send_from_directory, make_response, json, abort, redirect, url_for

app = Flask(__name__)

# Change the dictionary values to change the output file names. Don't change the keys unless you also update the rest of the dictionary references in
# the code
filenames = {
	"ongl": "onelinegridlab.png",
	"msgl": "milsofttogridlab.glm",
	"cygl": "cymetogridlab.glm",
	"glrun": "gridlabrun.json",
	"glgfm": "gridlabtogfm.gfm",
	"rungfm": "rungfm.txt",
	"samrun": "samrun.json",
	"tmomt": "transmissionmattoomt.json",
	"tmpf": "transmissionpowerflow.zip",
	"tv": "viewer.html",
	"dv": "distnetviz-viewer.html"
}


def get_abs_path(path):
	""" Return the absolute variant of the path argument. """
	if not os.path.isabs(path):
		path = "/" + path
	return path


def get_rel_path(path):
	""" Return the relative variant of the path argument. """
	return path.lstrip("/")


def get_task_metadata(temp_dir):
	"""
	Return metadata about the client's long-running task.

	Using start-time.txt will provide an accruate start time, but increases the response time of an HTTP request. Using getmtime() is faster than
	using start-time.txt, but isn't always accurate because mtime changes whenever a file is written/changed/deleted, so a file conversion task that
	writes multiple files can appear to have an elapsed time that resets. Inter-proces communication and tracking process communication times would be
	fastest, but difficult to implement.
	"""
	start_time_path = os.path.join(temp_dir, "start-time.txt")
	if os.path.isfile(start_time_path):
		with open(start_time_path) as f:
			start_time = float(f.read())
	else:
		start_time = os.path.getmtime(temp_dir) # Fallback in case start-time.txt doesn't exist for some reason
	elapsed_time = int(time.time() - start_time)
	elapsed_time = ("{:02}:{:02}:{:02}".format(elapsed_time // 3600, ((elapsed_time % 3600) // 60), elapsed_time % 60))
	metadata = {
		"Created at": time.ctime(os.path.getmtime(temp_dir)),
		"Elapsed time": elapsed_time,
	}
	error_path = os.path.join(temp_dir, "error.txt")
	if os.path.isfile(error_path):
		with open(error_path, 'r') as f:
			msg = f.readlines()
		metadata["Status"] = "Failed"
		metadata["Failure message"] = msg
	else:
		metadata["Status"] = "In-progress"
	return metadata


def get_download(func):
	""" Use the function argument to see if the process output exists in the filesystem """
	@wraps(func)
	def wrapper(*args, **kwargs):
		temp_dir = get_abs_path(kwargs["temp_dir"])
		response = func(temp_dir) # 404 is automatically raised
		threading.Timer(60.0, lambda: shutil.rmtree(temp_dir)).start()
		return response
	return wrapper


def get_status(func):
	""" Use the function argument to see if the task is finished """
	@wraps(func)
	def wrapper(*args, **kwargs):
		temp_dir = get_abs_path(kwargs["temp_dir"])
		if not os.path.isdir(temp_dir):
			abort(404)
		response = func(temp_dir)
		return json.jsonify(get_task_metadata(temp_dir)) if response is None else response
	return wrapper


def run_process(func):
	""" Use the function argument to run a file conversion process that is protected with try-except """
	@wraps(func)
	def wrapper(*args, **kwargs):
		temp_dir = args[0]
		try:
			with open(os.path.join(temp_dir, "start-time.txt"), 'w') as f:
				f.write(str(time.time()))
			func(temp_dir)
		except:
			with open(os.path.join(temp_dir, "error.txt"), 'w') as f:
				f.write(str(sys.exc_info()[1]))
	return wrapper

def start_process(func):
	""" Use the function argument to start a file conversion process """
	@wraps(func)
	# TODO: implement PID system to terminate processes (maybe never do this). We do it for web.py
    # Figure out a way to see how many processes are running on the server for testing?
	def wrapper(*args, **kwargs):
		temp_dir = tempfile.mkdtemp()
		p, response = func(temp_dir)
		p.start()
		return response 
	return wrapper


@app.route("/oneLineGridlab/<path:temp_dir>", methods=["DELETE"])
@app.route("/milsoftToGridlab/<path:temp_dir>", methods=["DELETE"])
@app.route("/cymeToGridlab/<path:temp_dir>", methods=["DELETE"])
@app.route("/gridlabRun/<path:temp_dir>", methods=["DELETE"])
@app.route("/gridlabdToGfm/<path:temp_dir>", methods=["DELETE"])
@app.route("/runGfm/<path:temp_dir>", methods=["DELETE"])
@app.route("/samRun/<path:temp_dir>", methods=["DELETE"])
@app.route("/transmissionMatToOmt/<path:temp_dir>", methods=["DELETE"])
@app.route("/transmissionPowerflow/<path:temp_dir>", methods=["DELETE"])
@app.route("/transmissionViz/<path:temp_dir>", methods=["DELETE"])
@app.route("/distributionViz/<path:temp_dir>", methods=["DELETE"])
def delete(temp_dir):
	temp_dir = get_abs_path(temp_dir)
	if not os.path.isdir(temp_dir):
		abort(404)
	metadata = get_task_metadata(temp_dir)
	if "Failure message" in metadata:
		del metadata["Failure message"]
	metadata["Status"] = "Stopped"
	metadata["Stopped at"] = time.ctime(time.time())
	shutil.rmtree(temp_dir)
	return json.jsonify(metadata)


@app.route("/oneLineGridlab", methods=["POST"])
@start_process
def oneLineGridlab_start(temp_dir):
	p = Process(target=oneLineGridlab, args=(temp_dir,))
	response = redirect(url_for("oneLineGridlab_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def oneLineGridlab(temp_dir):
	''' Data Params: {glm: [file], useLatLons: Boolean}
	OMF fuction: omf.feeder.latLonNxGraph()
	Runtime: should be around 1 to 30 seconds.
    Result: Create a one line diagram of the input glm. Return a .png of it. If useLatLons is True then draw using the lat/lons, otherwise force
    layout the graph. '''
	f = request.files['glm']
	glm_path = os.path.join(temp_dir, "in.glm")
	f.save(glm_path)
	feed = omf.feeder.parse(glm_path)
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
	plt.savefig(os.path.join(temp_dir, filenames["ongl"]))


@app.route("/oneLineGridlab/<path:temp_dir>")
@get_status
def oneLineGridlab_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["ongl"])):
		return redirect(url_for("oneLineGridlab_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/oneLineGridlab/<path:temp_dir>/download")
@get_download
def oneLineGridlab_download(temp_dir):
	return send_from_directory(temp_dir, filenames["ongl"])


@app.route('/milsoftToGridlab', methods=['POST'])
@start_process
def milsoftToGridlab_start(temp_dir):
	p = Process(target=milsoftToGridlab, args=(temp_dir,))
	response = redirect(url_for("milsoftToGridlab_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def milsoftToGridlab(temp_dir):
	'''Data Params: {std: [file], seq: [file]}
	Runtime: could take a couple minutes.
	OMF function: omf.milToGridlab.convert()
	Result: a .glm file converted from the two input files.'''
	stdPath = os.path.join(temp_dir, "in.std")
	request.files["std"].save(stdPath)
	seqPath = os.path.join(temp_dir, "in.seq")
	request.files["seq"].save(seqPath)
	with open(stdPath) as f:
		stdFile = f.read()
	with open(seqPath) as f:
		seqFile = f.read()
	tree = omf.milToGridlab.convert(stdFile, seqFile, rescale=True)
	with open(os.path.join(temp_dir, filenames["msgl"]), 'w') as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))


@app.route("/milsoftToGridlab/<path:temp_dir>")
@get_status
def milsoftToGridlab_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["msgl"])):
		return redirect(url_for("milsoftToGridlab_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/milsoftToGridlab/<path:temp_dir>/download")
@get_download
def milsoftToGridlab_download(temp_dir):
	return send_from_directory(temp_dir, filenames["msgl"], mimetype="text/plain")


@app.route("/cymeToGridlab", methods=["POST"])
@start_process
def cymeToGridlab_start(temp_dir):
	'''Data Params: {mdb: [file]}
	OMF function: omf.cymeToGridlab.convertCymeModel()
	Result: a .glm file converted from the input file.'''
	p = Process(target=cymeToGridlab, args=(temp_dir,))
	response = redirect(url_for("cymeToGridlab_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def cymeToGridlab(temp_dir):
	mdbPath = os.path.join(temp_dir, "in.mdb")
	request.files["mdb"].save(mdbPath)
	import locale
	locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
	tree = omf.cymeToGridlab.convertCymeModel(mdbPath, temp_dir)
	with open(os.path.join(temp_dir, filenames["cygl"]), 'w') as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))


@app.route("/cymeToGridlab/<path:temp_dir>")
@get_status
def cymeToGridlab_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["cygl"])):
		return redirect(url_for("cymeToGridlab_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/cymeToGridlab/<path:temp_dir>/download")
@get_download
def cymeToGridlab_download(temp_dir):
	return send_from_directory(temp_dir, filenames["cygl"], mimetype="text/plain")
	

@app.route("/gridlabRun", methods=["POST"])
@start_process
def gridlabRun_start(temp_dir):
	p = Process(target=gridlabRun, args=(temp_dir,))
	response = redirect(url_for("gridlabRun_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def gridlabRun(temp_dir):
	'''Data Params: {glm: [file]}
	Runtime: could take hours. Jeepers.
	OMF fuction: omf.solvers.gridlabd.runInFileSystem()
	Result: Run a GridLAB-D model and return the results as JSON.
	TODO: think about attachment support.'''
	fName = 'in.glm'
	f = request.files['glm']
	glmOnDisk = os.path.join(temp_dir, fName)
	f.save(glmOnDisk)
	feed = omf.feeder.parse(glmOnDisk)
	outDict = omf.solvers.gridlabd.runInFilesystem(feed, attachments=[], keepFiles=True, workDir=temp_dir, glmName='out.glm')
	with open(os.path.join(temp_dir, filenames["glrun"]), 'w') as f:
		json.dump(outDict, f)


@app.route("/gridlabRun/<path:temp_dir>")
@get_status
def gridlabRun_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["glrun"])):
		return redirect(url_for("gridlabRun_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/gridlabRun/<path:temp_dir>/download")
@get_download
def gridlabRun_download(temp_dir):
	return send_from_directory(temp_dir, filenames["glrun"], mimetype="application/json")


@app.route('/gridlabdToGfm', methods=['POST'])
@start_process
def gridlabdToGfm_start(temp_dir):
	p = Process(target=gridlabdToGfm, args=(temp_dir,))
	response = redirect(url_for("gridlabdToGfm_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def gridlabdToGfm(temp_dir):
	'''Data Params: {glm: [file], other_inputs: see source}
	OMF function: omf.models.resilientDist.convertToGFM()
	Runtime: should only be a couple seconds.
	Result: Convert the GridLAB-D model to a GFM model. Return the new id for the converted model. Note that this is not the main fragility model for
	GRIP.'''
	fName = 'in.glm'
	f = request.files['glm']
	glmPath = os.path.join(temp_dir, fName)
	f.save(glmPath)
	gfmInputTemplate = {
		'phase_variation': float(request.form.get('phase_variation')),
		'chance_constraint': float(request.form.get('chance_constraint')),
		'critical_load_met': float(request.form.get('critical_load_met')),
		'total_load_met': float(request.form.get('total_load_met')),
		'maxDGPerGenerator': float(request.form.get('max_dg_per_generator')),
		'dgUnitCost': float(request.form.get('dg_unit_cost')),
		'generatorCandidates': request.form.get('generator_candidates'),
		'criticalLoads': request.form.get('critical_loads')
	}
	for key, val in gfmInputTemplate.items():
		if val is None:
			raise Exception(("gridlabdToGfm was expecting a valid value for key: {key},"
				"but it received value: {value}").format(key=key, value=val))
	feederModel = {
		'nodes': [], # Don't need these.
		'tree': omf.feeder.parse(glmPath)
	}
	gfmDict = omf.models.resilientDist.convertToGFM(gfmInputTemplate, feederModel)
	with open(os.path.join(temp_dir, filenames["glgfm"]), 'w') as f:
		json.dump(gfmDict, f)


@app.route("/gridlabdToGfm/<path:temp_dir>")
@get_status
def gridlabdToGfm_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["glgfm"])):
		return redirect(url_for("gridlabdToGfm_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/gridlabdToGfm/<path:temp_dir>/download")
@get_download
def gridlabdToGfm_download(temp_dir):
	return send_from_directory(temp_dir, filenames["glgfm"], mimetype="application/json")


@app.route('/runGfm', methods=['POST'])
@start_process
def runGfm_start(temp_dir):
	p = Process(target=runGfm, args=(temp_dir,))
	response = redirect(url_for("runGfm_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def runGfm(temp_dir):
	''' Data Params: {gfm: [file], asc: [file]}
	OMF function: omf.solvers.gfm.run()
	Runtime: should be around 1 to 30 seconds.
	Result: Return the results dictionary/JSON from running LANL's General Fragility Model (GFM) on the input model and .asc hazard field. Note that
	this is not the main fragility model for GRIP. '''
	gfm_name = "gfm.json"
	gfm_path = os.path.join(temp_dir, gfm_name)
	request.files["gfm"].save(gfm_path)
	hazard_name = "hazard.asc"
	hazard_path = os.path.join(temp_dir, hazard_name)
	request.files["asc"].save(hazard_path)
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
		[javaCmd,'-jar', gfmBinaryPath, '-r', gfm_name, '-wf', hazard_name, '-num', '3', '-ro', outName],
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE,
		cwd = temp_dir
	)
	(stdout,stderr) = proc.communicate()
	gfmOutPath = os.path.join(temp_dir, outName)
	try:
		with open(gfmOutPath) as f:
			out = json.load(f)
	except:
		out = stdout
	with open(os.path.join(temp_dir, filenames["rungfm"]), 'w') as f:
		f.write(out)


@app.route("/runGfm/<path:temp_dir>")
@get_status
def runGfm_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["rungfm"])):
		return redirect(url_for("runGfm_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/runGfm/<path:temp_dir>/download")
@get_download
def runGfm_download(temp_dir):
	return send_from_directory(temp_dir, filenames["rungfm"])


@app.route('/samRun', methods=['POST'])
@start_process
def samRun_start(temp_dir):
	p = Process(target=samRun, args=(temp_dir,))
	response = redirect(url_for("samRun_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def samRun(temp_dir):
	'''Data Params: {tmy2: [file], [system advisor model inputs, approximately 30 floats]}
	OMF function: omf.solvers.sam.run()
	Runtime: should only be a couple seconds.
	Result: Run NREL's system advisor model with the specified parameters. Return the output vectors and floats in JSON'''
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
	with open(os.path.join(temp_dir, filenames["samrun"]), 'w') as f:
		json.dump(outData, f)


@app.route("/samRun/<path:temp_dir>")
@get_status
def samRun_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["samrun"])):
		return redirect(url_for("samRun_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/samRun/<path:temp_dir>/download")
@get_download
def samRun_download(temp_dir):
	return send_from_directory(temp_dir, filenames["samrun"])


@app.route('/transmissionMatToOmt', methods=['POST'])
@start_process
def transmissionMatToOmt_start(temp_dir):
	p = Process(target=transmissionMatToOmt, args=(temp_dir,))
	response = redirect(url_for("transmissionMatToOmt_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def transmissionMatToOmt(temp_dir):
	'''Data Params: {mat: [file], other_inputs: see source}
	OMF function: omf.network.parse()
	Runtime: maybe a couple minutes.
	Result: Convert the .m matpower model to an OMT (JSON-based) model. Return the model.'''
	mat_path = os.path.join(temp_dir, "input.m")
	request.files["matpower"].save(mat_path)
	omt_json = omf.network.parse(mat_path, filePath=True)
	if omt_json == {"baseMVA":"100.0","mpcVersion":"2.0","bus":{},"gen":{}, "branch":{}}:
		raise Exception("The submitted .m file was invalid or could not be parsed correctly.")
	nxG = omf.network.netToNxGraph(omt_json)
	omt_json = omf.network.latlonToNet(nxG, omt_json)
	with open(os.path.join(temp_dir, filenames["tmomt"]), 'w') as f:
		json.dump(omt_json, f)


@app.route("/transmissionMatToOmt/<path:temp_dir>")
@get_status
def transmissionMatToOmt_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["tmomt"])):
		return redirect(url_for("transmissionMatToOmt_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/transmissionMatToOmt/<path:temp_dir>/download")
@get_download
def transmissionMatToOmt_download(temp_dir):
	return send_from_directory(temp_dir, filenames["tmomt"])


@app.route('/transmissionPowerflow', methods=['POST'])
@start_process
def transmissionPowerflow_start(temp_dir):
	p = Process(target=transmissionPowerflow, args=(temp_dir,))
	response = redirect(url_for("transmissionPowerflow_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def transmissionPowerflow(temp_dir):
	'''Data Params: {omt: [file], other_inputs: see source}
	OMF function: omf.models.transmission.new and omf.models.transmission.work
	Runtime: tens of seconds.
	Result: TBD. '''
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
		"algorithm": request.form.get("algorithm") if request.form.get("algorithm") != "" else None,
		"model": request.form.get("model") if request.form.get("model") != "" else None,
		"tolerance": tolerance,
		"iteration": iteration,
		"genLimits": genLimits
	}
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
		with zipfile.ZipFile(os.path.join(model_dir, filenames["tmpf"]), 'w', zipfile.ZIP_DEFLATED) as z:
			z.write(os.path.join(model_dir, "output.png"), "output.png")
			z.write(os.path.join(model_dir, "allOutputData.json"), "allOutputData.json")
	else:
		raise Exception("Couldn't create model directory")


@app.route("/transmissionPowerflow/<path:temp_dir>")
@get_status
def transmissionPowerflow_status(temp_dir):
	model_dir = os.path.join(temp_dir, "transmission")
	if os.path.isfile(os.path.join(model_dir, filenames["tmpf"])):
		return redirect(url_for("transmissionPowerflow_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/transmissionPowerflow/<path:temp_dir>/download")
@get_download
def transmissionPowerflow_download(temp_dir):
	model_dir = os.path.join(temp_dir, "transmission")
	return send_from_directory(model_dir, filenames["tmpf"], as_attachment=True)


@app.route('/transmissionViz', methods=['POST'])
@start_process
def transmissionViz_start(temp_dir):
	p = Process(target=transmissionViz, args=(temp_dir,))
	response = redirect(url_for("transmissionViz_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def transmissionViz(temp_dir):
	'''Data Params: {omt: [file], other_inputs: see source}
	OMF function: omf.network.viz()
	Runtime: a couple seconds.
	Result: HTML interface visualizing the .omt file. '''
	omt_path = os.path.join(temp_dir, "in.omt")
	request.files["omt"].save(omt_path)
	try:
		with open(omt_path) as f:
			json.load(f)
	except:
		raise Exception("Could not parse the omt file as json")
	omf.network.get_HTML_interface_name(omt_path)


@app.route("/transmissionViz/<path:temp_dir>")
@get_status
def transmissionViz_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["tv"])):
		return redirect(url_for("transmissionViz_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/transmissionViz/<path:temp_dir>/download")
@get_download
def transmissionViz_download(temp_dir):
	return send_from_directory(temp_dir, filenames["tv"])


@app.route("/distributionViz", methods=["POST"])
@start_process
def distributionViz_start(temp_dir):
	p = Process(target=distributionViz, args=(temp_dir,))
	response = redirect(url_for("distributionViz_status", temp_dir=get_rel_path(temp_dir)), code=303)
	return (p, response)


@run_process
def distributionViz(temp_dir):
	'''Data Params: {omd: [file]} 
	OMF function: omf.distNetViz.viz()
	Runtime: a couple seconds.
	Result: HTML interface visualizing the .omd file. '''
	omd_path = os.path.join(temp_dir, "in.omd")
	request.files["omd"].save(omd_path)
	try:
		with open(omd_path) as f:
			json.load(f)
	except:
		raise Exception("Could not parse omd file as json")
	omf.distNetViz.viz(omd_path, outputPath=temp_dir, outputName=filenames["dv"], open_file=False)


@app.route("/distributionViz/<path:temp_dir>")
@get_status
def distributionViz_status(temp_dir):
	if os.path.isfile(os.path.join(temp_dir, filenames["dv"])):
		return redirect(url_for("distributionViz_download", temp_dir=get_rel_path(temp_dir)), code=303)


@app.route("/distributionViz/<path:temp_dir>/download")
@get_download
def distributionViz_download(temp_dir):
	return send_from_directory(temp_dir, filenames["dv"])


def serve_production():
	""" Make sure to run this file with the -m (module) flag. One way to kill gunicorn is with $ ps -ef | awk '/gunicorn/ {print $2}' | xargs kill """
	os.chdir(os.path.dirname(__file__))
	subprocess.call(["gunicorn", "-w", "4", "-b", "0.0.0.0:5100", "--preload", "-k sync", "grip:app"])


def serve_development():
	"""
	gevent does NOT work with multiprocessing. Don't use gevent or gunicorn with gevent in this version of the API.
	"""
	app.run(debug=True, port=5100)


if __name__ == '__main__':
	serve_production()