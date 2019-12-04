''' Web server exposing HTTP API for GRIP. '''
import omf
import os, traceback, tempfile, platform, subprocess, zipfile, subprocess, time, shutil, sys, threading, datetime, numbers
from functools import wraps
from multiprocessing import Process
import matplotlib.pyplot as plt
from flask import Flask, request, send_from_directory, make_response, json, abort, redirect, url_for, jsonify
from grip_config import Config


app = Flask(__name__)
app.config.from_object(Config)


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
	"tv": "network-viewer.html",
	"dv": "distnetviz-viewer.html"
}


def _get_abs_path(path):
	'''Return the absolute variant of the path argument.''' 
	if not os.path.isabs(path):
		path = "/" + path
	return path


def _get_rel_path(path):
	'''Return the relative variant of the path argument.'''
	return path.lstrip("/")


def _get_elapsed_time(start, end):
	'''TODO'''
	elapsed_time = int(end - start)
	return '{:02}:{:02}:{:02}'.format(elapsed_time // 3600, ((elapsed_time % 3600) // 60), elapsed_time % 60)


def _get_created_at(temp_dir):
	'''TODO'''
	start_time_path = os.path.join(temp_dir, 'start-time.txt')
	created_at = os.path.getmtime(start_time_path)
	return created_at


def _get_timestamp(unix_time):
	'''Return an ISO 8601 timestamp string that is equivalent to a Unix time integer'''
	return datetime.datetime.utcfromtimestamp(unix_time).isoformat().rsplit('.')[0] + 'Z'


def _get_failure_time(temp_dir):
	'''TODO'''
	error_path = os.path.join(temp_dir, 'error.txt')
	if os.path.isfile(error_path):
		stopped_at = os.path.getmtime(error_path)
		with open(error_path, 'r') as f:
			msg = f.readlines()
		if app.config["DELETE_FAILED_JOBS"]:
			shutil.rmtree(temp_dir)
		return (stopped_at, msg)
	return (None, None)


def _validate_input(input_metadata):
	'''TODO'''
	name = input_metadata['name']
	input_type = input_metadata['type']
	input_ = request.files.get(name) if input_type == 'file' else request.form.get(name)
	if input_ is None:
		if input_metadata['required']:
			return ({ name: None }, "The parameter '{}' of type '{}' is required, but it was not submitted.".format(name, input_type))
		return (None, None)
	elif input_type != 'file':
		try:
			if input_type is bool:
				if input_ != 'True' and input_ != 'False':
					raise Exception
			else:
				input_ = input_type(input_)
		except:
			return ({ name: input_}, "The parameter '{}' could not be converted into the required type '{}'.".format(name, input_type))
		input_range = input_metadata.get('range')
		if input_range is not None:
			if issubclass(input_type, str):	
				if input_ not in input_range:
					return ({ name: input_ }, "The parameter '{}' was not one of the allowed values: '{}'.".format(name, input_range))
			elif issubclass(input_type, numbers.Number):
				min = input_range.get('min')
				if min is not None and input_ < min:
					return ({ name: input_ }, "The parameter '{}' was less than the minimum bound of '{}'.".format(name, min))
				max = input_range.get('max')
				if max is not None and input_ > max:
					return ({ name: input_ }, "The parameter '{}' was greater than the maximum bound of '{}'.".format(name, max))
	return (None, None)


def start_process(route_function=None, inputs_metadata=None, custom_validation_functions=None):
	'''TODO'''
	def decorator(process_function):
		@wraps(process_function)
		def wrapper(*args, **kwargs):
			'''If the inputs were valid, start the process and return 202 and JSON, else return 4xx and JSON.'''
			errors = []
			if inputs_metadata:
				for i in inputs_metadata:
					src, msg = _validate_input(i)
					if msg:
						errors.append({
							'http code': 400,
							'source': src,
							'title': 'Invalid Parameter Value',
							'detail': msg
						})
			if len(errors) > 0:
				r = jsonify(job={'state': 'failed'}, errors=errors)
				r.status = '400'
				return r
			temp_dir = tempfile.mkdtemp()
			if custom_validation_functions:
				for func in custom_validation_functions:
					src, msg = func(temp_dir)
					if msg:
						errors.append({
							'http code': 422,
							'source': src,
							'title': 'Invalid Parameter Value Combination',
							'detail': msg
						})
			if len(errors) > 0:
				r = jsonify(job={'state': 'failed'}, errors=errors)
				r.status = '422'
				return r
			start_time_path = os.path.join(temp_dir, 'start-time.txt')
			with open(start_time_path, 'w'):
				pass
			created_at = _get_created_at(temp_dir)	
			url = process_function(temp_dir)
			r = jsonify(job={
				'state': 'in-progress',
				'status': os.path.join(request.url_root, _get_rel_path(url)),
				'created at': _get_timestamp(created_at),
				'elapsed time': '00:00:00',
			})
			r.status = '202'
			return r
		return wrapper
	if route_function is None:
		return decorator 
	else:
		return decorator(route_function)


def try_except(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		'''Try-except the the function.'''
		temp_dir = args[0]
		try:
			func(temp_dir)
		except:
			entries = traceback.format_exception(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
			with open(os.path.join(temp_dir, 'error.txt'), 'w') as f:
				f.write(entries[-0])
				f.write(entries[-2])
				f.write(entries[-1])
	return wrapper


def get_status(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		'''Return JSON indicating the status of the background job if it exists, else 404.'''
		temp_dir = _get_abs_path(kwargs["temp_dir"])
		if not os.path.isdir(temp_dir):
			abort(404)
		created_at = _get_created_at(temp_dir)
		failed_at, failure_msg = _get_failure_time(temp_dir)
		completed_at, status_url, download_url = func(temp_dir)	
		status_url = os.path.join(request.url_root, _get_rel_path(status_url))
		download_url = os.path.join(request.url_root, _get_rel_path(download_url))
		response_data = {'job': {'created at': _get_timestamp(created_at)}}
		if failed_at:
			state = 'failed'
			elapsed_time = _get_elapsed_time(created_at, failed_at)
			response_data['job']['stopped at'] = _get_timestamp(failed_at)
			response_data['errors'] = [{
				'http code': 500,
				'source': failure_msg,
				'title': 'Job Failed',
				'detail': 'The process handling the job raised an exception.'
			}]
		elif completed_at:
			state = 'complete'
			elapsed_time = _get_elapsed_time(created_at, completed_at)
			response_data['job']['stopped at'] = _get_timestamp(completed_at)
			response_data['job']['download'] = download_url
		else:
			state = 'in-progress'
			elapsed_time = _get_elapsed_time(created_at, time.time())
		response_data['job']['elapsed time'] = elapsed_time
		if request.method == 'DELETE':
			state = 'deleted'
			if response_data['job'].get('stopped at') is None:
				response_data['job']['stopped at'] = _get_timestamp(time.time())
			del response_data['job']['download']
			shutil.rmtree(temp_dir)
		elif request.method == 'GET':
			response_data['job']['status'] = status_url
		response_data['job']['state'] = state
		r = jsonify(response_data)
		if failed_at:
			r.status = '500'
		return r
	return wrapper


def get_download(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		'''Return the requested resource if it exists, else 404.'''
		temp_dir = _get_abs_path(kwargs["temp_dir"])
		response = func(temp_dir)
		if app.config["DELETE_SUCCESSFUL_JOBS"]:
			shutil.rmtree(temp_dir)
		return response
	return wrapper


def _validate_oneLineGridlab(temp_dir):
	'''TODO'''
	glm_path = os.path.join(temp_dir, 'in.glm')
	request.files['glm'].save(glm_path)
	if not omf.distNetViz.contains_coordinates(omf.feeder.parse(glm_path)) and request.form['useLatLons'] == 'True':
		return (
			{'useLatLons': 'True'},
			("Since the submitted GLM contained no coordinates, 'useLatLons' must be 'False' because artificial coordinates must be used to draw"
			" the GLM.")
		)
	return (None, None)


@app.route("/oneLineGridlab", methods=["POST"])
@start_process(
	inputs_metadata=(
		{'name': 'useLatLons', 'required': True, 'type': bool},
		{'name': 'glm', 'required': True, 'type': 'file'}
	),
	custom_validation_functions=(_validate_oneLineGridlab,)
)
def oneLineGridlab_start(temp_dir):
	p = Process(target=oneLineGridlab, args=(temp_dir,))
	p.start()
	return url_for('oneLineGridlab_status', temp_dir=_get_rel_path(temp_dir))


@try_except
def oneLineGridlab(temp_dir):
	'''
	Create a one-line diagram of the input GLM and return a PNG of it.

	Form parameters:
	:param glm: a GLM file.
	:param useLatLons: 'True' if the diagram should be drawn with coordinate values taken from within the GLM, 'False' if the diagram should be drawn
		with artificial coordinates using Graphviz NEATO.

	Details:
	:OMF fuction: omf.feeder.latLonNxGraph().
	:run-time: about 1 to 30 seconds.
	''' 
	glm_path = os.path.join(temp_dir, 'in.glm')
	feed = omf.feeder.parse(glm_path)
	graph = omf.feeder.treeToNxGraph(feed)
	neatoLayout = True if request.form.get('useLatLons') == 'False' else False
	# Clear old plots.
	plt.clf()
	plt.close()
	# Plot new plot.
	omf.feeder.latLonNxGraph(graph, labels=False, neatoLayout=neatoLayout, showPlot=False)
	plt.savefig(os.path.join(temp_dir, filenames["ongl"]))


@app.route("/oneLineGridlab/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def oneLineGridlab_status(temp_dir):
	ongl_path = os.path.join(temp_dir, filenames['ongl'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('oneLineGridlab_status', temp_dir=temp_dir)
	download_url = url_for("oneLineGridlab_download", temp_dir=temp_dir)
	if os.path.isfile(ongl_path):
		return (os.path.getmtime(ongl_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/oneLineGridlab/<path:temp_dir>/download")
@get_download
def oneLineGridlab_download(temp_dir):
	return send_from_directory(temp_dir, filenames["ongl"])


@app.route('/milsoftToGridlab', methods=['POST'])
@start_process(
	inputs_metadata=(
		{'name': 'std', 'required': True, 'type': 'file'},
		{'name': 'seq', 'required': True, 'type': 'file'}
	)
)
def milsoftToGridlab_start(temp_dir):
	p = Process(target=milsoftToGridlab, args=(temp_dir,))
	p.start()
	return url_for('milsoftToGridlab_status', temp_dir=_get_rel_path(temp_dir))


@try_except
def milsoftToGridlab(temp_dir):
	'''
	Convert a Milsoft Windmil ASCII export (.std & .seq) in to a GridLAB-D .glm and return the .glm.

	Form parameters:
	:param std: an STD file.
	:param seq: an SEQ file.

	Details:
	:OMF function: omf.milToGridlab.convert().
	:run-time: up to a few minutes
	'''
	stdPath = os.path.join(temp_dir, 'in.std')
	request.files['std'].save(stdPath)
	seqPath = os.path.join(temp_dir, 'in.seq')
	request.files['seq'].save(seqPath)
	with open(stdPath) as f:
		stdFile = f.read()
	with open(seqPath) as f:
		seqFile = f.read()
	tree = omf.milToGridlab.convert(stdFile, seqFile, rescale=True)
	with open(os.path.join(temp_dir, filenames['msgl']), 'w') as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))


@app.route('/milsoftToGridlab/<path:temp_dir>', methods=['GET', 'DELETE'])
@get_status
def milsoftToGridlab_status(temp_dir):
	msgl_path = os.path.join(temp_dir, filenames['msgl'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('milsoftToGridlab_status', temp_dir=temp_dir)
	download_url = url_for('milsoftToGridlab_download', temp_dir=temp_dir)
	if os.path.isfile(msgl_path):
		return (os.path.getmtime(msgl_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/milsoftToGridlab/<path:temp_dir>/download")
@get_download
def milsoftToGridlab_download(temp_dir):
	return send_from_directory(temp_dir, filenames["msgl"], mimetype="text/plain")


@app.route("/cymeToGridlab", methods=["POST"])
@start_process(inputs_metadata=({'name': 'mdb', 'required': True, 'type': 'file'},))
def cymeToGridlab_start(temp_dir):
	p = Process(target=cymeToGridlab, args=(temp_dir,))
	p.start()
	return url_for('cymeToGridlab_status', temp_dir=_get_rel_path(temp_dir))


@try_except
def cymeToGridlab(temp_dir):
	'''
	Convert an Eaton Cymdist .mdb export in to a GridLAB-D .glm and return the .glm.

	Form parameters:
	:param mdb: a MDB file.

	Details:
	:OMF function: omf.cymeToGridlab.convertCymeModel().
	:run-time: up to a few minutes.
	'''
	mdbPath = os.path.join(temp_dir, "in.mdb")
	request.files["mdb"].save(mdbPath)
	import locale
	locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
	tree = omf.cymeToGridlab.convertCymeModel(mdbPath, temp_dir)
	with open(os.path.join(temp_dir, filenames["cygl"]), 'w') as outFile:
		outFile.write(omf.feeder.sortedWrite(tree))


@app.route("/cymeToGridlab/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def cymeToGridlab_status(temp_dir):
	cygl_path = os.path.join(temp_dir, filenames['cygl'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('cymeToGridlab_status', temp_dir=temp_dir)
	download_url = url_for("cymeToGridlab_download", temp_dir=temp_dir)
	if os.path.isfile(cygl_path):
		return (os.path.getmtime(cygl_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/cymeToGridlab/<path:temp_dir>/download")
@get_download
def cymeToGridlab_download(temp_dir):
	return send_from_directory(temp_dir, filenames["cygl"], mimetype="text/plain")
	

@app.route("/gridlabRun", methods=["POST"])
@start_process(inputs_metadata=({'name': 'glm', 'required': True, 'type': 'file'},))
def gridlabRun_start(temp_dir):
	p = Process(target=gridlabRun, args=(temp_dir,))
	p.start()
	return url_for('gridlabRun_status', temp_dir=_get_rel_path(temp_dir))


@try_except
def gridlabRun(temp_dir):
	'''
	Run a .glm through GridLAB-D and return the results as JSON.

	Form parameters:
	:param glm: a GLM file.

	Details:
	:OMF fuction: omf.solvers.gridlabd.runInFileSystem().
	:run-time: up to a few hours.
	TODO: think about attachment support.
	'''
	fName = 'in.glm'
	f = request.files['glm']
	glmOnDisk = os.path.join(temp_dir, fName)
	f.save(glmOnDisk)
	feed = omf.feeder.parse(glmOnDisk)
	outDict = omf.solvers.gridlabd.runInFilesystem(feed, attachments=[], keepFiles=True, workDir=temp_dir, glmName='out.glm')
	with open(os.path.join(temp_dir, filenames["glrun"]), 'w') as f:
		json.dump(outDict, f)


@app.route("/gridlabRun/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def gridlabRun_status(temp_dir):
	glrun_path = os.path.join(temp_dir, filenames['glrun'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('gridlabRun_status', temp_dir=temp_dir)
	download_url = url_for('gridlabRun_download', temp_dir=temp_dir)
	if os.path.isfile(glrun_path):
		return (os.path.getmtime(glrun_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/gridlabRun/<path:temp_dir>/download")
@get_download
def gridlabRun_download(temp_dir):
	return send_from_directory(temp_dir, filenames["glrun"], mimetype="application/json")


@app.route('/gridlabdToGfm', methods=['POST'])
@start_process(
	inputs_metadata=(
		{'name': 'glm', 				'required': True,  'type': 'file'},
		{'name': 'phase_variation', 	'required': False, 'type': float, 'range': {'min': 0, 'max': 1}},
		{'name': 'chance_constraint', 	'required': False, 'type': float, 'range': {'min': 0, 'max': 1}}, 
		{'name': 'critical_load_met', 	'required': False, 'type': float, 'range': {'min': 0, 'max': 1}},
		{'name': 'total_load_met', 		'required': False, 'type': float, 'range': {'min': 0, 'max': 1}},
		{'name': 'maxDGPerGenerator', 	'required': False, 'type': float},
		{'name': 'dgUnitCost', 			'required': False, 'type': float},
		{'name': 'generatorCandidates', 'required': False, 'type': str},
		{'name': 'criticalLoads', 		'required': False, 'type': str},
	)
)
def gridlabdToGfm_start(temp_dir):
	p = Process(target=gridlabdToGfm, args=(temp_dir,))
	p.start()
	return url_for("gridlabdToGfm_status", temp_dir=_get_rel_path(temp_dir))


@try_except
def gridlabdToGfm(temp_dir):
	'''
	Convert a GridLAB-D model (i.e. .glm file) into a LANL ANSI General Fragility Model and return the GFM model as JSON. Note that this is not the
	main fragility model for GRIP.

	Form parameters:
	:param glm: a GLM file.
	:param phase_variation: maximum phase unbalance allowed in the optimization model.
	:param chance_constraint: indicates the percent of damage scenarios where load constraints above must be met.
	:param critical_load_met: indicates the percent of critical load that must be met in each damage scenario. 
	:param total_load_met: indicates the percent of non-critical load that must be met in each damage scenario. 
	:param maxDGPerGenerator: the maximum DG capacity that a generator supports in MW. 
	:param dgUnitCost: the cost of adding distributed generation to a load in $/MW.
	:param generatorCandidates: the IDs of nodes on the system where the user wants to consider adding distributed generation. At least one node is
		required.
	:type generatorCandidates: one long string delimited with commas.
	:param criticalLoads: the IDs of loads on the system that the user declares to be critical (must-run).
	:type criticalLoads: one long string delimited with commas.

	Details:
	:OMF function: omf.models.resilientDist.convertToGFM().
	:run-time: a few seconds.
	'''
	fName = 'in.glm'
	f = request.files['glm']
	glmPath = os.path.join(temp_dir, fName)
	f.save(glmPath)
	gfmInputTemplate = {
		'phase_variation': float(request.form.get('phase_variation', 0.15)),
		'chance_constraint': float(request.form.get('chance_constraint', 1)),
		'critical_load_met': float(request.form.get('critical_load_met', .98)),
		'total_load_met': float(request.form.get('total_load_met', .9)),
		'maxDGPerGenerator': float(request.form.get('max_dg_per_generator', 1)),
		'dgUnitCost': float(request.form.get('dg_unit_cost', 1000000)),
		'generatorCandidates': request.form.get('generator_candidates', ''),
		'criticalLoads': request.form.get('critical_loads', '')
	}
	feederModel = {
		'nodes': [], # Don't need these.
		'tree': omf.feeder.parse(glmPath)
	}
	gfmDict = omf.models.resilientDist.convertToGFM(gfmInputTemplate, feederModel)
	with open(os.path.join(temp_dir, filenames["glgfm"]), 'w') as f:
		json.dump(gfmDict, f)


@app.route("/gridlabdToGfm/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def gridlabdToGfm_status(temp_dir):
	glgfm_path = os.path.join(temp_dir, filenames['glgfm'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('gridlabdToGfm_status', temp_dir=temp_dir)
	download_url = url_for('gridlabdToGfm_download', temp_dir=temp_dir)
	if os.path.isfile(glgfm_path):
		return (os.path.getmtime(glgfm_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/gridlabdToGfm/<path:temp_dir>/download")
@get_download
def gridlabdToGfm_download(temp_dir):
	return send_from_directory(temp_dir, filenames["glgfm"], mimetype="application/json")


@app.route('/runGfm', methods=['POST'])
@start_process(
	inputs_metadata=(
		{'name': 'gfm', 'required': True, 'type': 'file'},
		{'name': 'asc', 'required': True, 'type': 'file'}
	)
)
def runGfm_start(temp_dir):
	p = Process(target=runGfm, args=(temp_dir,))
	p.start()
	return url_for('runGfm_status', temp_dir=_get_rel_path(temp_dir))


@try_except
def runGfm(temp_dir):
	'''
	Calculate distribution damage using a LANL ANSI General Fragility Model file (i.e. a .gfm) along with a hazard field file (i.e. a .asc file) and
	return the results as JSON. Note that this is not the main fragility model for GRIP. 

	Form parameters:
	:param gfm: a GFM file.
	:param asc: an ASC file.

	Details:
	:OMF function: omf.solvers.gfm.run().
	:run-time: should be around 1 to 30 seconds.
	'''
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


@app.route("/runGfm/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def runGfm_status(temp_dir):
	rungfm_path = os.path.join(temp_dir, filenames['rungfm'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('runGfm_status', temp_dir=temp_dir)
	download_url = url_for('runGfm_download', temp_dir=temp_dir)
	if os.path.isfile(rungfm_path):
		return (os.path.getmtime(rungfm_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/runGfm/<path:temp_dir>/download")
@get_download
def runGfm_download(temp_dir):
	return send_from_directory(temp_dir, filenames["rungfm"])


@app.route('/samRun', methods=['POST'])
@start_process(
	inputs_metadata=(
		{'name': 'tmy2', 		'required': True,  'type': 'file'},
		{'name': 'system_size', 'required': False, 'type': int},
		{'name': 'derate', 		'required': False, 'type': float, 'range': {'min': 0, 'max': 1}},
		{'name': 'track_mode', 	'required': False, 'type': int,   'range': {'min': 0, 'max': 3}},
		{'name': 'azimuth', 	'required': False, 'type': float, 'range': {'min': 0, 'max': 360}},
		{'name': 'tilt', 		'required': False, 'type': float, 'range': {'min': 0, 'max': 90}},
	)
)
def samRun_start(temp_dir):
	p = Process(target=samRun, args=(temp_dir,))
	p.start()
	return url_for("samRun_status", temp_dir=_get_rel_path(temp_dir))


@try_except
def samRun(temp_dir):
	'''
	Run NREL's System Advisor Model with the specified parameters and return output vectors and floats in JSON.

	Form parameters:
	:param tmy2: a tmy2 file.
	:param system_size: nameplate capacity.
	:param derate: system derate value.
	:param track_mode: tracking mode.
	:param azimuth: azimuth angle.
	:param tilt: tilt angle.
	There are 40 other additional optional input parameters to the pvwattsv1 module of S.A.M.

	Details:
	:OMF function: omf.solvers.sam.run().
	:run-time: should only be a couple of seconds.
	See pvwattsv1-variable-info.txt for details on other 40 possible inputs to this route.
	'''
	tmy2_path = os.path.join(temp_dir, "in.tmy2")
	request.files["tmy2"].save(tmy2_path)
	# Set up SAM data structures.
	ssc = omf.solvers.nrelsam2013.SSCAPI()
	dat = ssc.ssc_data_create()
	# Set the inputs.
	ssc.ssc_data_set_string(dat, "file_name", tmy2_path)
	for key in request.form.keys():
		ssc.ssc_data_set_number(dat, key, float(request.form.get(key)))
	# Enter required parameters
	system_size = int(request.form.get('system_size', 4))
	ssc.ssc_data_set_number(dat, 'system_size', system_size)
	derate = float(request.form.get('derate', .77))
	ssc.ssc_data_set_number(dat, 'derate', derate)
	track_mode = int(request.form.get('track_mode', 0))
	ssc.ssc_data_set_number(dat, 'track_mode', track_mode)
	azimuth = float(request.form.get('azimuth', 180))
	ssc.ssc_data_set_number(dat, 'azimuth', azimuth)
	tilt = float(request.form.get('tilt', 30))
	ssc.ssc_data_set_number(dat, 'tilt', tilt)
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


@app.route("/samRun/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def samRun_status(temp_dir):
	samrun_path = os.path.join(temp_dir, filenames['samrun'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('samRun_status', temp_dir=temp_dir)
	download_url = url_for('samRun_download', temp_dir=temp_dir)
	if os.path.isfile(samrun_path):
		return (os.path.getmtime(samrun_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/samRun/<path:temp_dir>/download")
@get_download
def samRun_download(temp_dir):
	return send_from_directory(temp_dir, filenames["samrun"])


@app.route('/transmissionMatToOmt', methods=['POST'])
@start_process(inputs_metadata=({'name': 'matpower', 'required': True, 'type': 'file'},))
def transmissionMatToOmt_start(temp_dir):
	p = Process(target=transmissionMatToOmt, args=(temp_dir,))
	p.start()
	return url_for('transmissionMatToOmt_status', temp_dir=_get_rel_path(temp_dir))


@try_except
def transmissionMatToOmt(temp_dir):
	'''
	Convert a MATPOWER .mat or .m input into a JSON .omt transmission circuit format and return the .omt.

	Form parameters:
	:param matpower: a MATPOWER .mat file.

	Details:
	:OMF function: omf.network.parse()
	:run-time: maybe a couple minutes.
	'''
	mat_path = os.path.join(temp_dir, "input.mat")
	request.files["matpower"].save(mat_path)
	omt_json = omf.network.parse(mat_path, filePath=True)
	if omt_json == {"baseMVA":"100.0","mpcVersion":"2.0","bus":{},"gen":{}, "branch":{}}:
		raise Exception("The submitted .m file was invalid or could not be parsed correctly.")
	nxG = omf.network.netToNxGraph(omt_json)
	omt_json = omf.network.latlonToNet(nxG, omt_json)
	with open(os.path.join(temp_dir, filenames["tmomt"]), 'w') as f:
		json.dump(omt_json, f)


@app.route("/transmissionMatToOmt/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def transmissionMatToOmt_status(temp_dir):
	tmomt_path = os.path.join(temp_dir, filenames['tmomt'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('transmissionMatToOmt_status', temp_dir=temp_dir)
	download_url = url_for('transmissionMatToOmt_download', temp_dir=temp_dir)
	if os.path.isfile(tmomt_path):
		return (os.path.getmtime(tmomt_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/transmissionMatToOmt/<path:temp_dir>/download")
@get_download
def transmissionMatToOmt_download(temp_dir):
	return send_from_directory(temp_dir, filenames["tmomt"])


@app.route('/transmissionPowerflow', methods=['POST'])
@start_process(
	inputs_metadata=(
		{'name': 'algorithm', 'required': False, 'type': str, 'range': ('NR', 'FDXB', 'FDBX', 'GS')},
		{'name': 'model', 	  'required': False, 'type': str, 'range': ('AC', 'DC')},
		{'name': 'iteration', 'required': False, 'type': int, 'range': {'min': 1}},
		{'name': 'tolerance', 'required': False, 'type': float},
		{'name': 'genLimits', 'required': False, 'type': int, 'range': {'min': 0, 'max': 2}}
	)
)
def transmissionPowerflow_start(temp_dir):
	p = Process(target=transmissionPowerflow, args=(temp_dir,))
	p.start()
	return url_for("transmissionPowerflow_status", temp_dir=_get_rel_path(temp_dir))


@try_except
def transmissionPowerflow(temp_dir):
	'''
	Run ACOPF for a .omt transmission circuit.

	Form parameters:
	:param omt: an OMT file.
	:param algorithm: powerflow solution method. 'NR' = Newton's method, 'FDXB' = Fast-Decoupled (XB version), 'FDBX' = Fast-Decouple (BX version),
		'GS' = Gauss-Seidel.
	:param model: AC vs. DC modeling for power flow and OPF formulation.
	:param iteration: maximum number of iterations allowed in the attempt to find a powerflow solution.
	:param tolerance: termination tolerance on per unit P and Q dispatch.
	:param genLimits: enforce gen reactive power limits at expense of Vm. 0 = do not enforce limits, 1 = enforce limits, simultaneous bus type
		conversion, 2 = enforce limits, one-at-a-time bus type conversion.

	Details:
	:OMF function: omf.models.transmission.new() and omf.models.transmission.work().
	:run-time: tens of seconds.
	'''
	algorithm = request.form.get('algorithm', 'NR')
	model = request.form.get('model', 'AC')
	iteration = int(request.form.get('iteration', 10))
	tolerance = float(request.form.get('tolerance', 10**-8))
	genLimits = int(request.form.get('genLimits', 0))
	inputDict = {
		'algorithm': algorithm,
		'model': model,
		'tolerance': tolerance,
		'iteration': iteration,
		'genLimits': genLimits
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


@app.route("/transmissionPowerflow/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def transmissionPowerflow_status(temp_dir):
	tmpf_path = os.path.join(temp_dir, 'transmission', filenames['tmpf'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('transmissionPowerflow_status', temp_dir=temp_dir)
	download_url = url_for('transmissionPowerflow_download', temp_dir=temp_dir)
	if os.path.isfile(tmpf_path):
		return (os.path.getmtime(tmpf_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/transmissionPowerflow/<path:temp_dir>/download")
@get_download
def transmissionPowerflow_download(temp_dir):
	model_dir = os.path.join(temp_dir, "transmission")
	return send_from_directory(model_dir, filenames["tmpf"], as_attachment=True)


@app.route('/transmissionViz', methods=['POST'])
@start_process(inputs_metadata=({'name': 'omt', 'required': True, 'type': 'file'},))
def transmissionViz_start(temp_dir):
	p = Process(target=transmissionViz, args=(temp_dir,))
	p.start()
	return url_for("transmissionViz_status", temp_dir=_get_rel_path(temp_dir))


@try_except
def transmissionViz(temp_dir):
	'''
	Generate an interactive and editable one line diagram of a transmission network and return it as an HTML file.

	Form parameters:
	:param omt: an .omt file.

	Details:
	:OMF function: omf.network.viz().
	:run-time: a couple seconds.
	'''
	omt_path = os.path.join(temp_dir, "in.omt")
	request.files["omt"].save(omt_path)
	try:
		with open(omt_path) as f:
			json.load(f)
	except:
		raise Exception("Could not parse the omt file as json")
	omf.network.viz(omt_path, output_path=temp_dir, output_name=filenames["tv"], open_file=False)


@app.route("/transmissionViz/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def transmissionViz_status(temp_dir):
	tv_path = os.path.join(temp_dir, filenames['tv'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('transmissionViz_status', temp_dir=temp_dir)
	download_url = url_for("transmissionViz_download", temp_dir=temp_dir)
	if os.path.isfile(tv_path):
		return (os.path.getmtime(tv_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/transmissionViz/<path:temp_dir>/download")
@get_download
def transmissionViz_download(temp_dir):
	return send_from_directory(temp_dir, filenames["tv"])


@app.route("/distributionViz", methods=["POST"])
@start_process(inputs_metadata=({'name': 'omd', 'required': True, 'type': 'file'},))
def distributionViz_start(temp_dir):
	p = Process(target=distributionViz, args=(temp_dir,))
	p.start()
	return url_for("distributionViz_status", temp_dir=_get_rel_path(temp_dir))


@try_except
def distributionViz(temp_dir):
	'''
	Generate an interactive and editable one line diagram of a distribution network and return it as an HTML file.

	Form parameters:
	:param omd: a .omd file.

	Details:
	:OMF function: omf.distNetViz.viz().
	:run-time: a few seconds.
	'''
	omd_path = os.path.join(temp_dir, "in.omd")
	request.files["omd"].save(omd_path)
	try:
		with open(omd_path) as f:
			json.load(f)
	except:
		raise Exception("Could not parse omd file as json")
	omf.distNetViz.viz(omd_path, outputPath=temp_dir, outputName=filenames["dv"], open_file=False)


@app.route("/distributionViz/<path:temp_dir>", methods=['GET', 'DELETE'])
@get_status
def distributionViz_status(temp_dir):
	dv_path = os.path.join(temp_dir, filenames['dv'])
	temp_dir = _get_rel_path(temp_dir)
	status_url = url_for('distributionViz_status', temp_dir=temp_dir)
	download_url = url_for("distributionViz_download", temp_dir=temp_dir)
	if os.path.isfile(dv_path):
		return (os.path.getmtime(dv_path), status_url, download_url)
	return (None, status_url, download_url)


@app.route("/distributionViz/<path:temp_dir>/download")
@get_download
def distributionViz_download(temp_dir):
	return send_from_directory(temp_dir, filenames["dv"])


def serve_production():
	'''
	- Make sure to run this file with the -m (module) flag
	- One way to kill gunicorn is with $ ps -ef | awk '/gunicorn/ {print $2}' | xargs kill
	'''
	os.chdir(os.path.dirname(__file__))
	subprocess.call(["gunicorn", "-w", "4", "-b", "0.0.0.0:5100", "--preload", "-k sync", "grip:app"])


def serve_development():
	'''gevent does NOT work with multiprocessing. Don't use gevent or gunicorn with gevent in this version of the API.'''
	app.run(debug=False, port=5100)


if __name__ == '__main__':
	serve_production()