# Prereq: `pip install 'git+https://github.com/NREL/ditto.git@master#egg=ditto[all]'`
import os
from os.path import join as pJoin
import subprocess
import json
import warnings
import traceback
from omf import feeder, distNetViz
import random
import math
from time import time
import re
import shutil
import tempfile
import networkx as nx
import omf

def cyme_to_dss(cyme_dir, out_path, inter_dir=None):
	''' Converts cyme txt files into an opendss file with nrel/ditto.
	Need equipment.txt, load.txt, and network.txt in cyme_dir '''
	if inter_dir:
		tdir = inter_dir
	else:
		tdir = tempfile.mkdtemp()
	print('Ditto Conversion Dir:', tdir)
	root = os.path.abspath(cyme_dir)
	cmd = f'ditto-cli convert --from cyme --input "{root}" --to opendss --output {tdir}'
	os.system(cmd)
	dss_to_clean_via_save(f'{tdir}/Master.dss', out_path)

def gld_to_dss(glm_path, out_path, inter_dir=None):
	''' Converts GridLAB-D files to opendss with nrel/ditto'''
	if inter_dir:
		tdir = inter_dir
	else:
		tdir = tempfile.mkdtemp()
	print('Ditto Conversion Dir:', tdir)
	root = os.path.abspath(glm_path)
	cmd = f'ditto-cli convert --from glm --input "{root}" --to opendss --output {tdir}'
	os.system(cmd)
	dss_to_clean_via_save(f'{tdir}/Master.dss', out_path)

def dss_to_gld(opendss_path, out_path, inter_dir=None):
	''' Converts opendss files to GridLAB-D with nrel/ditto'''
	#TODO: test.
	if inter_dir:
		tdir = inter_dir
	else:
		tdir = tempfile.mkdtemp()
	print('Ditto Conversion Dir:', tdir)
	root = os.path.abspath(opendss_path)
	cmd = f'ditto-cli convert --from opendss --input "{root}" --to glm --output {tdir}'
	os.system(cmd)
	dss_to_clean_via_save(f'{tdir}/Master.dss', out_path)

def dss_to_clean_via_save(dss_file, clean_out_path, add_pf_syntax=True, clean_up=False):
	'''Updated function for OpenDSS v1.7.4 which does everything differently from earlier versions...
	Converts raw OpenDSS circuit definition files to the *.clean.dss syntax required by OMF.
	This version uses the opendss save functionality to better preserve dss syntax.'''
	#TODO: Detect missing makebuslist, since windmil and others leave it out.
	#TODO: Fix repeated wdg= keys!?!?!?
	# Execute opendss's save command reliably on a circuit. opendssdirect fails at this.
	import os, re, shutil, subprocess
	dirname = os.path.dirname(dss_file)
	shutil.rmtree(f'{dirname}/SAVED_DSS', ignore_errors=True)
	# Make a dss file that can reliably save a dang circuit.
	contents = open(dss_file,'r').read()
	contents += '\nsave circuit dir=SAVED_DSS'
	with open(f'{dirname}/saver.dss','w') as saver_file:
		saver_file.write(contents)
	# Run that saver file.
	subprocess.run(['opendsscmd', 'saver.dss'], cwd=dirname)
	dss_folder_path = f'{dirname}/SAVED_DSS'
	# Get the object files.
	ob_files = os.listdir(f'{dss_folder_path}')
	ob_files = sorted(ob_files)
	# Generate clean each of the object files.
	clean_copies = {}
	print('All files detected:',ob_files)
	for fname in ob_files:
		if os.path.isfile(f'{dss_folder_path}/{fname}'):
			with open(f'{dss_folder_path}/{fname}', 'r') as ob_file:
				ob_data = ob_file.read().lower() # lowercase everything
				ob_data = ob_data.replace('"', '') # remove quote characters
				ob_data = ob_data.replace('\t', ' ') # tabs to spaces
				ob_data = re.sub(r' +', r' ', ob_data) # remove consecutive spaces
				ob_data = re.sub(r'(^ +| +$)', r'', ob_data) # remove leading and trailing whitespace
				ob_data = ob_data.replace('\n~', '') # remove tildes
				ob_data = re.sub(r' *, *', r',', ob_data) # remove spaces around commas
				ob_data = re.sub(r', *(\]|\))', r'\1', ob_data) # remove empty final list items
				ob_data = re.sub(r' +\| +', '|', ob_data) # remove spaces around bar characters
				ob_data = re.sub(r'(\[|\() *', r'\1', ob_data) # remove spaces after list start
				ob_data = re.sub(r' *(\]|\))', r'\1', ob_data) # remove spaces before list end
				ob_data = re.sub(r'(new|edit) ', r'\1 object=', ob_data) # add object= key
				ob_data = re.sub(r'(\d) +(\d|\-)', r'\1,\2', ob_data) # replace space-separated lists with comma-separated
				ob_data = re.sub(r'(\d) +(\d|\-)', r'\1,\2', ob_data) # HACK: second space-sep replacement to make sure it works
				ob_data = re.sub(r'zipv=([\d\.\-,]+)', r'zipv=(\1)', ob_data) # HACK: fix zipv with missing parens
				ob_data = re.sub(r'(redirect |buscoords |giscoords |makebuslist)', r'!\1', ob_data) # remove troublesome Master.dss redirects.
				clean_copies[fname.lower()] = ob_data
	# Special handling for buscoords
	if 'buscoords.dss' in clean_copies:
		bus_data = clean_copies['buscoords.dss']
		nice_buses = re.sub(r'([\w_\-\.]+),([\w_\-\.]+),([\w_\-\.]+)', r'setbusxy bus=\1 x=\2 y=\3', bus_data)
		clean_copies['buscoords.dss'] = 'makebuslist\n' + nice_buses
	#HACK: This is the order in which things need to be inserted or opendss errors out. Lame!
	CANONICAL_DSS_ORDER = ['master.dss', 'vsource.dss', 'transformer.dss', 'reactor.dss', 'regcontrol.dss', 'cndata.dss', 'wiredata.dss', 'linecode.dss', 'spectrum.dss', 'swtcontrol.dss', 'tcc_curve.dss', 'capacitor.dss', 'loadshape.dss', 'growthshape.dss', 'line.dss', 'generator.dss', 'load.dss', 'buscoords.dss', 'busvoltagebases.dss']
	# Note files we got that aren't in canonical files:
	for fname in clean_copies:
		if fname not in CANONICAL_DSS_ORDER:
			print(f'File available but ignored: {fname}')
	# Construct output from files, ignoring master, which is bugged in opendss as of 2023-01-17
	clean_out = ''
	for fname in CANONICAL_DSS_ORDER:
		if fname not in clean_copies:
			print(f'Missing file: {fname}')
		clean_out += f'\n\n!!!{fname}\n'
		clean_out += clean_copies[fname]
	clean_out = clean_out.lower()
	# Optional: include a slug of code to run powerflow
	if add_pf_syntax:
		powerflow_slug = '\n\n!powerflow code\nset maxiterations=1000\nset maxcontroliter=1000\ncalcv\nsolve\nshow quantity=voltage'
		clean_out = clean_out + powerflow_slug
	# Optional: remove intermediate files and write a single clean file.
	if clean_up:
		shutil.rmtree(dss_folder_path, ignore_errors=True)
	with open(clean_out_path, 'w') as out_file:
		out_file.write(clean_out)

def _old_dss_to_clean_via_save(dss_file, clean_out_path, add_pf_syntax=True, clean_up=False):
	'''Works with OpenDSS versions<1.7.4.
	Converts raw OpenDSS circuit definition files to the *.clean.dss syntax required by OMF.
	This version uses the opendss save functionality to better preserve dss syntax.'''
	#TODO: Detect missing makebuslist, since windmil and others leave it out.
	#TODO: Fix repeated wdg= keys!?!?!?
	# Execute opendss's save command reliably on a circuit. opendssdirect fails at this.
	dirname = os.path.dirname(dss_file)
	shutil.rmtree(f'{dirname}/SAVED_DSS', ignore_errors=True)
	# Make a dss file that can reliably save a dang circuit.
	contents = open(dss_file,'r').read()
	contents += '\nsave circuit dir=SAVED_DSS'
	with open(f'{dirname}/saver.dss','w') as saver_file:
		saver_file.write(contents)
	# Run that saver file.
	subprocess.run(['opendsscmd', 'saver.dss'], cwd=dirname)
	dss_folder_path = f'{dirname}/SAVED_DSS'
	# Get master file.
	master = open(f'{dss_folder_path}/Master.dss').readlines()
	master = [x for x in master if x != '\n']
	# Get the object files.
	ob_files = os.listdir(f'{dss_folder_path}')
	ob_files = sorted(ob_files)
	ob_files.remove('Master.dss')
	# Clean each of the object files.
	clean_copies = {}
	print('OB_FILES!',ob_files)
	for fname in ob_files:
		if os.path.isfile(f'{dss_folder_path}/{fname}'):
			with open(f'{dss_folder_path}/{fname}', 'r') as ob_file:
				ob_data = ob_file.read().lower() # lowercase everything
				ob_data = ob_data.replace('"', '') # remove quote characters
				ob_data = ob_data.replace('\t', ' ') # tabs to spaces
				ob_data = re.sub(r' +', r' ', ob_data) # remove consecutive spaces
				ob_data = re.sub(r'(^ +| +$)', r'', ob_data) # remove leading and trailing whitespace
				ob_data = ob_data.replace('\n~', '') # remove tildes
				ob_data = re.sub(r' *, *', r',', ob_data) # remove spaces around commas
				ob_data = re.sub(r', *(\]|\))', r'\1', ob_data) # remove empty final list items
				ob_data = re.sub(r' +\| +', '|', ob_data) # remove spaces around bar characters
				ob_data = re.sub(r'(\[|\() *', r'\1', ob_data) # remove spaces after list start
				ob_data = re.sub(r' *(\]|\))', r'\1', ob_data) # remove spaces before list end
				ob_data = re.sub(r'(new|edit) ', r'\1 object=', ob_data) # add object= key
				ob_data = re.sub(r'(\d) +(\d|\-)', r'\1,\2', ob_data) # replace space-separated lists with comma-separated
				ob_data = re.sub(r'(\d) +(\d|\-)', r'\1,\2', ob_data) # HACK: second space-sep replacement to make sure it works
				ob_data = re.sub(r'zipv=([\d\.\-,]+)', r'zipv=(\1)', ob_data) # HACK: fix zipv with missing parens
				clean_copies[fname.lower()] = ob_data
	# Special handline for buscoords
	if 'buscoords.dss' in clean_copies:
		bus_data = clean_copies['buscoords.dss']
		nice_buses = re.sub(r'([\w_\-\.]+),([\w_\-\.]+),([\w_\-\.]+)', r'setbusxy bus=\1 x=\2 y=\3', bus_data)
		clean_copies['buscoords.dss'] = nice_buses
	# Construct the clean single file output.
	clean_out = ''
	for line in master:
		ob_file_name = re.findall(r'\w+\.[dD][sS][sS]', line)
		if ob_file_name == []:
			if line.startswith('New Circuit.'):
				line = 'new object=circuit.' + line[12:]
			clean_out += line
		else:
			clean_out += f'\n!{line}'
			clean_out += clean_copies[ob_file_name[0].lower()]
	clean_out = clean_out.lower()
	# Optional: include a slug of code to run powerflow
	if add_pf_syntax:
		powerflow_slug = '\n\n!powerflow code\nset maxiterations=1000\nset maxcontroliter=1000\ncalcv\nsolve\nshow quantity=voltage'
		clean_out = clean_out + powerflow_slug
	# Optional: remove intermediate files and write a single clean file.
	if clean_up:
		shutil.rmtree(dss_folder_path, ignore_errors=True)
	with open(clean_out_path, 'w') as out_file:
		out_file.write(clean_out)

def dssCleanLists(pathToDss):
	'''Helper function to go through dss file and reformat lists (rmatrix, xmatrix, 
	mult, buses, conns, kvs, kvas) with commas and no spaces'''
	with open(pathToDss, 'r') as dssFile:
		contents = dssFile.readlines()
	fixedContents = []
	for line in contents:
		lineItems = line.split()
		openedList = False
		lineString = ""
		for item in lineItems:
			if lineString == "":
				#first item in line
				lineString = lineString + item
			else:
				listOpeners = [ '(' , '[' , '{' ]
				listClosers = [ ')' , ']' , '}' ]
				hasOpener = [x for x in listOpeners if(x in item)]
				hasCloser = [x for x in listClosers if(x in item)]
				noCommas = [ '(' , '[' , '{' , ',' , '|' ]
				if '=' in item:
					lineString = lineString + " " + item
					if hasCloser:
						openedList = False
					elif hasOpener:
						openedList = True
				elif openedList:
					if (lineString[-1] in noCommas) or (item[0] in listClosers) or (item[0] == '|'):
						lineString = lineString + item
					else:
						lineString = lineString + ',' + item
					if hasCloser:
						openedList = False
				else:
					lineString = lineString + " " + item
					if hasOpener and not hasCloser:
						openedList = True
		fixedContents.append(lineString)
	outPath = pathToDss[:-4] + "_cleanLists.dss"
	with open(outPath, 'w') as outFile:
		for fixedLine in fixedContents:
			outFile.write(f'{fixedLine}\n')


def dssToTree(pathToDss):
	''' Convert a .dss file to an in-memory, OMF-compatible 'tree' object.
	Note that we only support a VERY specifically-formatted DSS file.'''
	# TODO: Consider removing the handling for 'wdg=' syntax within this block, as we will not support it in an input file. 
	# Ingest file.
	with open(pathToDss, 'r') as dssFile:
		contents = dssFile.readlines()
	# Lowercase everything. OpenDSS is case insensitive.
	contents = [x.lower() for x in contents]
	# Clean up the file.
	for i, line in enumerate(contents):
		# Remove whitespace.
		contents[i] = line.strip()
		# Comment removal
		bangLoc = line.find('!')
		if bangLoc != -1:
			contents[i] = line[:bangLoc]
		# Join using the tilde (~) syntax
		if line.startswith('~'):
			# Look back to find the first line with content.
			for j in range(i - 1, 0, -1):
				if contents[j] != '':
					contents[j] = contents[j] + contents[i].replace('~', ' ')
					contents[i] = ''
					break
	# Capture original line numbers and drop blanks
	contents = dict([(c,x) for (c, x) in enumerate(contents) if x != ''])
	# Lex it
	convTbl = {'bus':'buses', 'conn':'conns', 'kv':'kvs', 'kva':'kvas', '%r':'%r'}
	# convTbl = {'bus':'buses', 'conn':'conns', 'kv':'kvs', 'kva':'kvas', '%r':'%rs'} # TODO at some point this will need to happen; need to check what is affected i.e. viz, etc

	from collections import OrderedDict 
	for i, line in contents.items():
		jpos = 0
		try:
			contents[i] = line.split()
			ob = OrderedDict() 
			ob['!CMD'] = contents[i][0]
			if len(contents[i]) > 1:
				for j in range(1, len(contents[i])):
					jpos = j
					splitlen = len(contents[i][j].split('='))
					k,v=('','',)
					if splitlen==3:
						print('OMF does not support OpenDSS\'s \'file=\' syntax for defining property values.')
						k,v,f = contents[i][j].split('=')
						# replaceFileSyntax() # DEBUG
						## replaceFileSyntax  should do the following:
						  # parse the filename (contained in v)
						  # read in the file and parse as array
						  # v = file content array, cast as a string
					else:
						k,v = contents[i][j].split('=')
					# TODO: Should we pull the multiwinding transformer handling out of here and put it into dssFilePrep()?
					if k == 'wdg':
						continue
					if (k in ob.keys()) or (convTbl.get(k,k) in ob.keys()): # if the single key already exists in the object, then this is the second pass. If pluralized key exists, then this is the 2+nth pass
						# pluralize the key if needed, get the existing values, add the incoming value, place into ob, remove singular key
						plurlk = convTbl.get(k, None) # use conversion table to pluralize the key or keep same key
						incmngVal = v
						xistngVals = []
						if k in ob: # indicates 2nd winding, existing value is a string (in the case of %r, this indicates 3rd winding as well!)
							if (type(ob[k]) != tuple) or (type(ob[k]) != list): # pluralized values can be defined as either
							#if iter(type(ob[k])):
								xistngVals.append(ob[k])
								del ob[k]
						if plurlk in ob: # indicates 3rd+ winding; existing values are tuples
								for item in ob[plurlk]:
									xistngVals.append(item)
						xistngVals.append(incmngVal) # concatenate incoming value with the existing values
						ob[plurlk] =  tuple(xistngVals) # convert all to tuple
					else: # if single key has not already been added, add it
						ob[k] = v
		except:
			raise Exception(f'\nError encountered in group (space delimited) #{jpos+1} of line {i + 1}: {line}')
			# raise Exception("Temp fix but error in loop at line 76")
		contents[i] = ob
	# Print to file
	#with open('dssTreeRepresentation.csv', 'w') as outFile:
	#	ii = 1
	#	for k,v in contents.items():
	#		outFile.write(str(k) + '\n')
	#		ii = ii + 1
	#		for k2,v2 in v.items():
	#			outFile.write(',' + str(k2) + ',' + str(v2) + '\n')
	return list(contents.values())

def treeToDss(treeObject, outputPath):
	outFile = open(outputPath, 'w')
	for ob in treeObject:
		line = ob['!CMD']
		for key in ob:
			if not key.startswith('!'):
				line = f"{line} {key}={ob[key]}"
			if key.startswith('!TEST'):
				line = f"{line} {ob['!TEST']}"
		outFile.write(line + '\n')
	outFile.close()

def _dssFilePrep(fpath):
	'''***DO NOT USE*** 
	**There are no future plans to widen dss parsing rules beyond the specifically-formatted
	.dss files that are expected by omf (described in OMF docs). This function is only left here in 
	case an OMF developer wants to generate some new test files from something that is badly 
	formatted to begin with.**
	Prepares an OpenDSS circuit definition file (.dss) for consumption by the 
	OMF. The expected input is the path to a .dss master file that redirects to or
	compiles from other .dss files within the same directory. The path can also 
	indicate a single .dss file that does not contain redirect or compile commands.'''
	
	import opendssdirect as dss
	import pandas as pd
	import tempfile as tf
	from omf.solvers.opendss import runDssCommand

	# Note that tmpdir is not automatically cleaned up on premature exit; This is expected to be addressed by user action. 
	with tf.TemporaryDirectory() as tempDir:
		dssFilePath = os.path.realpath(fpath)
		dssDirPath, dssFileName = os.path.split(dssFilePath)
		try:
			with open(dssFilePath):
				pass
		except Exception as ex:
			print('While accessing the file located at %s, the following exception occured: %s'%(dssDirPath, ex))
		runDssCommand('Clear')
		x = runDssCommand('Redirect "' + dssFilePath + '"')
		x = runDssCommand('Solve')
		# TODO: If runDSS() is changed to return dssFileLoc, replace the above lines of code with this:
		#  dssDirPath = self.runDSS(fpath, keep_output=False) # will require moving the function or changing the definition to reference 'self".
	
		exptDirPath = tempDir + '/' + 'OmfCktExport'
		runDssCommand('Save Circuit ' + 'purposelessFileName.dss "' + exptDirPath + '"')
		# Manipulate buscoords file to create commands that generate bus list
		coords = pd.read_csv(exptDirPath + '/BusCoords.dss', header=None, dtype=str, names=['Element', 'X', 'Y'])
		coordscmds = []
		for i,x in coords.iterrows():
			elmt = x['Element']
			xcoord = x['X']
			ycoord = x['Y']
			coordscmds.append('SetBusXY bus=' + str(elmt) + ' X=' + str(xcoord) + ' Y=' + str(ycoord) + '\n') # save commands for later usage
		# Get Master.DSS from exported files and insert content from other files
		outfilepath = dssDirPath + '/' + dssFileName[:-4] + '_expd.dss'
		with open(exptDirPath + '/Master.DSS', 'r') as ogMaster, open(outfilepath, 'a') as catMaster:
			catMaster.truncate(0)
			for line in ogMaster:
				# wherever there is a redirect or a compile, get the code from that file and insert into catMaster
				try:
					if line.lower().startswith('redirect') or line.lower().startswith('compile'):
						catMaster.write('! ' + line)
						addnFilename = line.split(' ')[1] # get path of file to insert (accounts for inline comments following the command)
						addnFilename = ' '.join(addnFilename.splitlines()) # removes newline characters
						with open(exptDirPath + '/' + addnFilename, 'r') as addn: # will error if file is not located in same directory as Master.dss
							addn = addn.read()
							z = catMaster.write(addn)
					elif line.lower().startswith('buscoords'):
						catMaster.write('! ' + line)
						catMaster.writelines(coordscmds)
					else:
						catMaster.write(line)
				except Exception as ex:
					print(ex)
			catMaster.flush() # really shouldn't have to do this, but addresses an apparent delay (due to buffering) if this file is read immediately after this fnxn returns
			respath = _applyRegex(catMaster.name)
		os.remove(outfilepath)
		return os.path.abspath(respath) # still might not be clean. Round trip through treetoDss(dssToTree(respath), respath) to fix problems with transformer winding definitions

def _applyRegex(fpath):
	'''***DO NOT USE***
	**There are no future plans to widen dss parsing rules beyond the specifically-formatted
	.dss files that are expected by omf (described in OMF docs). This function is only left here in 
	case an OMF developer wants to generate some new test files from something that is badly 
	formatted to begin with. Meant to be called on files that end with '_expd.dss' **'''

	import re
	with open(fpath, 'r') as inFile, open(fpath[:-9]+'_clean.dss', 'w') as outFile:
		# apply all dat ugly regex
		# The ^ (begins with) regex syntax does not work here.
		contents = inFile.read()
		contents = re.sub('New (?!object=)', 'New object=', contents)
		contents = re.sub('Edit (?!object=)', 'Edit object=', contents)
		contents = re.sub('\)', ']', contents)
		contents = re.sub('\(', '[', contents)
		contents = re.sub('(?<=\d)(\s)+(?=\d)', ',', contents)
		contents = re.sub('(?<=\d)(\s)+(?=-\d)', ',', contents)
		contents = re.sub('(\s)+\|(\s)+', '|', contents)
		contents = re.sub('\[(\s)*', '[', contents)
		contents = re.sub('(\s)*\]', ']', contents)
		contents = re.sub('"', '', contents)
		contents = re.sub('(?<=\w)(\s)*,(\s)+(?=\w)', ',', contents)
		contents = re.sub('(?<=\w)(\s)*,(\s)+(?=-\w)', ',', contents)
		contents = re.sub('(?<=\w)(\s)+,(\s)*(?=\w)', ',', contents)
		contents = re.sub('(?<=\w)(\s)+,(\s)*(?=-\w)', ',', contents)
		contents = re.sub(',(\s)*(?=\])', '', contents)
		# The following are best applied by hand because busnames are so varied
		#contents = re.sub('(?<=buses=\[\w*),', '.1.2.3,', contents)
		#contents = re.sub('(?<=buses=\[\w*(\.\d)*,\w*)\]', '.1.2.3]', contents)
		#contents = re.sub('(?<=buses=\[\w*(\.\d)*,\w*),', '.1.2.3,', contents)
		#contents = re.sub('(?<=bus(\w?)=\w*) ', '.1.2.3 ', contents) #'bus(\w?)' captures bus, bus1, bus2
		#contents = re.sub('(?<=bus(\w?)=\w*-\w*) ', '.1.2.3 ', contents) #'bus(\w?)' captures bus, bus1, bus2 with hyphen within
		#contents = re.sub('rdcohms=.* ','',contents) # removes rdcohms=stuff
		#contents = re.sub('wdg=.* ','',contents) # removes wdg=stuff
		#contents = re.sub('%r=.* ','',contents) # removes %R=stuff
		#contents = re.sub('(?<=taps=\[\d,\d,\d\] ).*(?=taps=)','',contents) # handles repeated stuff between 'taps' and 'taps'
		outFile.write(contents)
		return outFile.name

def _dfToListOfDicts(dfin, objtype):
	'''Converts the contents of a data frame into a list of dictionaries, where each
		dictionary represents a single row, with keys corresponding to the column names.'''
		#TODO: mapping for attribute renaming dss<->tree (use objtype for this)
	#print(dfin.head(1))
	dictlst = []
	dfin.rename(columns={'Name':'Object'}, inplace=True)
	#TODO add any other attribute name conversions
	#TODO: change any lists to tuples?
	for name, obj in dfin.iterrows(): #TODO refactor for performance (very slow to iterate over rows. vectorize?)
		obj['Object'] = objtype + '.' + str(name)
		obj_dict = dict(zip(obj.index,obj))
		dictlst.append(obj_dict)
	return dictlst

def _extend_with_exc(from_d, to_d, exclude_list):
	''' Add all items in from_d to to_d that aren't in exclude_list. '''
	good_items = {k: from_d[k] for k in from_d if k not in exclude_list}
	to_d.update(good_items)

def evilDssTreeToGldTree(dssTree):
	''' World's worst and ugliest converter. Hence evil. 
	We built this to do quick-and-dirty viz of openDSS files. '''
	gldTree = {}
	g_id = 1
	# Build bad gld representation of each object
	bus_names = []
	bus_with_coords = []
	# Handle all the components.
	for ob in dssTree:
		try:
			if ob['!CMD'] == 'setbusxy':
				gldTree[str(g_id)] = {
					'object': 'bus',
					'name': ob['bus'],
					'latitude': ob['y'],
					'longitude': ob['x']
				}
				bus_with_coords.append(ob['bus'])
			elif ob['!CMD'] == 'new':
				obtype, name = ob['object'].split('.')
				if 'bus1' in ob and 'bus2' in ob:
					# line-like object. includes reactors.
					fro, froCode = ob['bus1'].split('.', maxsplit=1)
					to, toCode = ob['bus2'].split('.', maxsplit=1)
					gldTree[str(g_id)] = {
						'object': obtype,
						'name': name,
						'from': fro,
						'to': to,
						'!FROCODE': '.' + froCode,
						'!TOCODE': '.' + toCode
					}
					bus_names.extend([fro, to])
					stuff = gldTree[str(g_id)]
					_extend_with_exc(ob, stuff, ['object','bus1','bus2','!CMD'])
				elif 'buses' in ob:
					#transformer-like object.
					bb = ob['buses']
					bb = bb.replace(']','').replace('[','').split(',')
					b1 = bb[0]
					fro, froCode = b1.split('.', maxsplit=1)
					ob['!FROCODE'] = '.' + froCode
					b2 = bb[1]
					to, toCode = b2.split('.', maxsplit=1)
					ob['!TOCODE'] = '.' + toCode
					gldobj = {
						'object': obtype,
						'name': name,
						'from': fro,
						'to': to
					}
					bus_names.extend([fro, to])
					if len(bb)==3:
						b3 = bb[2]
						to2, to2Code = b3.split('.', maxsplit=1)
						ob['!TO2CODE'] = '.' + to2Code
						gldobj['to2'] = to2
						bus_names.append(to2)
					gldTree[str(g_id)] = gldobj
					_extend_with_exc(ob, gldTree[str(g_id)], ['object','buses','!CMD'])
				elif 'bus' in ob:
					#load-like object.
					bus_root, connCode = ob['bus'].split('.', maxsplit=1)
					gldTree[str(g_id)] = {
						'object': obtype,
						'name': name,
						'parent': bus_root,
						'!CONNCODE': '.' + connCode
					}
					bus_names.append(bus_root)
					_extend_with_exc(ob, gldTree[str(g_id)], ['object','bus','!CMD'])
				elif 'bus1' in ob and 'bus2' not in ob:
					#load-like object, alternate syntax
					try:
						bus_root, connCode = ob['bus1'].split('.', maxsplit=1)
						ob['!CONNCODE'] = '.' + connCode
					except:
						bus_root = ob['bus1'] # this shoudln't happen if the .clean syntax guide is followed.
					gldTree[str(g_id)] = {
						'object': obtype,
						'name': name,
						'parent': bus_root,
					}
					bus_names.append(bus_root)
					_extend_with_exc(ob, gldTree[str(g_id)], ['object','bus1','!CMD'])
				elif 'element' in ob:
					#control object (connected to another object instead of a bus)
					#cobtype, cobname, connCode = ob['element'].split('.', maxsplit=2)
					cobtype, cobname = ob['element'].split('.', maxsplit=1)
					# if obtype == 'capcontrol':
					# 	obparent = ob['capacitor']
					# else:
					# 	obparent = cobtype + '.' + cobname
					obparent = cobtype + '.' + cobname
					gldTree[str(g_id)] = {
						'object': obtype,
						'name': name,
						'parent': obparent,
					}
					_extend_with_exc(ob, gldTree[str(g_id)], ['object','element','!CMD'])
				else:
					#config-like object
					gldTree[str(g_id)] = {
						'object': obtype,
						'name': name
					}
					_extend_with_exc(ob, gldTree[str(g_id)], ['object','!CMD'])
			elif ob.get('object','').split('.')[0]=='vsource':
				obtype, name = ob['object'].split('.')
				conn, connCode = ob.get('bus1').split('.', maxsplit=1)
				gldTree[str(g_id)] = {
					'object': obtype,
					'name': name,
					'parent': conn,
					'!CONNCODE': '.' + connCode
				}
				_extend_with_exc(ob, gldTree[str(g_id)], ['object','bus1'])
			elif ob['!CMD']=='edit':
				#TODO: handle edited objects? maybe just extend the 'new' block (excluding vsource) because the functionality is basically the same.
				warnings.warn(f"Ignored 'edit' command: {ob}")
			elif ob['!CMD'] not in ['new', 'setbusxy', 'edit']: # what about 'set', 
				#command-like objects.
				gldTree[str(g_id)] = {
					'object': '!CMD',
					'name': ob['!CMD']
				}
				_extend_with_exc(ob, gldTree[str(g_id)], ['!CMD'])
			else:
				warnings.warn(f"Ignored {ob}")
			g_id += 1
		except:
			raise Exception(f"\n\nError encountered on parsing object {ob}\n")
	# Warn on buses with no coords.
	#no_coord_buses = set(bus_names) - set(bus_with_coords)
	#if len(no_coord_buses) != 0:
		#warnings.warn(f"Buses without coordinates:{no_coord_buses}")
	return gldTree

def evilGldTreeToDssTree(evil_gld_tree):
	''' Inverse frontend to DSS converter. Still evil. '''
	dssTree = []
	# Put objects in order.
	all_objs = evil_gld_tree.items()
	objs_in_order = [y[1] for y in sorted(all_objs, key=lambda x:int(x[0]))]
	# Process each object.
	for ob in objs_in_order:
		if ob.get('object') == 'bus':
			new_ob = {
				'!CMD':'setbusxy',
				'bus':ob['name'],
				'x': ob['longitude'],
				'y': ob['latitude']
			}
			dssTree.append(new_ob)
		elif ob.get('object') == 'line':
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob['name'],
				'bus1': ob['from'] + ob.get('!FROCODE',''),
				'bus2': ob['to']+ ob.get('!TOCODE',''),
			}
			_extend_with_exc(ob, new_ob, ['!CMD','from','to','name','object','latitude','longitude','!FROCODE', '!TOCODE'])
			dssTree.append(new_ob)
		elif ob.get('object') == 'transformer':
			buses = f"[{ob['from']}{ob.get('!FROCODE','')},{ob['to']}{ob.get('!TOCODE','')}]" # for 2-winding xfrmrs
			exclist = ['!CMD','from','to','to2','name','object','latitude','longitude','!FROCODE','!TOCODE','windings']
			if ob.get('to2'): # for 3-winding xfrmrs
				exclist.extend(['to2','!TO2CODE'])
				buses = f"[{ob['from']}{ob.get('!FROCODE','')},{ob['to']}{ob.get('!TOCODE','')},{ob['to2']}{ob.get('!TO2CODE','')}]"
			#if ob.get('to3'): # for 4-winding xfrmrs (rare)
			#	exclist.extend(['to3','!TO3CODE'])
			#	buses = f"[{ob['from']}{ob.get('!FROCODE','')},{ob['to']}{ob.get('!TOCODE','')},{ob['to2']}{ob.get('!TO2CODE','')},{ob['to3']}{ob.get('!TO3CODE','')}]"
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob['name'],
			}
			if ob.get('windings','NWP')!='NWP':
				new_ob['windings'] = ob['windings'] # This is required to ensure correct order (because the 'windings' property triggers memory allocation and resets everything to default values)
			new_ob['buses'] = buses # 'buses' must come after 'windings', if existing.
			_extend_with_exc(ob, new_ob, exclist)
			dssTree.append(new_ob)
		elif ob.get('object') == 'reactor':
			#TODO: this block of code is same as for 'line' above. Consider combining.
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob['name'],
				'bus1': ob['from'] + ob.get('!FROCODE',''),
				'bus2': ob['to']+ ob.get('!TOCODE',''),
			}
			_extend_with_exc(ob, new_ob, ['!CMD','from','to','name','object','latitude','longitude','!FROCODE', '!TOCODE'])
			dssTree.append(new_ob)
		elif ob.get('object') == 'regcontrol':
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob.get('name',''),
			}
			if ob.get('parent','NP')!='NP':
				if ob.get('!CONNCODE','NCC')=='NCC':
					new_ob['!CONNCODE'] = '.1' # If no node info is specified, then it defaults to one-phase.
				new_ob['bus'] = ob['parent'] + ob['!CONNCODE']
			_extend_with_exc(ob, new_ob, ['parent','name','object','latitude','longitude','!CONNCODE'])
			dssTree.append(new_ob)
		elif ob.get('object') == 'capcontrol':
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob.get('name',''),
				'element': ob['parent'] + ob.get('!CONNCODE', '')
			}
			_extend_with_exc(ob, new_ob, ['parent','name','object','latitude','longitude','!CONNCODE'])
			dssTree.append(new_ob)
		elif ob.get('object') == 'energymeter':
			#TODO this block of code is the same as 'capcontrol' above. Consider combining.
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob.get('name',''),
				'element': ob['parent'] + ob.get('!CONNCODE', '')
			}
			_extend_with_exc(ob, new_ob, ['parent','name','object','latitude','longitude','!CONNCODE'])
			dssTree.append(new_ob)
		elif ob.get('object') == 'monitor':
			#TODO this block of code is the same as 'capcontrol' above. Consider combining.
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob.get('name',''),
				'element': ob['parent'] + ob.get('!CONNCODE', '')
			}
			_extend_with_exc(ob, new_ob, ['parent','name','object','latitude','longitude','!CONNCODE'])
			dssTree.append(new_ob)
		elif 'parent' in ob:
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob.get('name',''),
				'bus1': ob['parent'] + ob.get('!CONNCODE', '')
			}
			_extend_with_exc(ob, new_ob, ['parent','name','object','latitude','longitude','!CONNCODE'])
			dssTree.append(new_ob)
		elif 'bus' not in ob and 'bus1' not in ob and 'bus2' not in ob and 'buses' not in ob and ob.get('object') != '!CMD':
			# floating config type object.
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob['name'],
			}
			_extend_with_exc(ob, new_ob, ['!CMD','name','object','latitude','longitude'])
			dssTree.append(new_ob)
		elif ob.get('object') == '!CMD':
			new_ob = {
				'!CMD': ob['name'],
			}
			_extend_with_exc(ob, new_ob, ['!CMD', 'name', 'object','latitude','longitude'])
			dssTree.append(new_ob)
		else:
			print(f"Unprocessed object: {ob}")
			# warnings.warn(f"Unprocessed object: {ob}")
	return dssTree

def evilToOmd(evilTree, outPath):
	omdStruct = dict(feeder.newFeederWireframe)
	omdStruct['syntax'] = 'DSS'
	omdStruct['tree'] = evilTree
	with open(outPath, 'w') as outFile:
		json.dump(omdStruct, outFile, indent=4)

def _name_to_key(glm):
	''' Make fast lookup map by name in a glm.
	WARNING: if the glm changes, the map will no longer be valid.'''
	mapping = {}
	for key, val in glm.items():
		if 'name' in val:
			mapping[val['name']] = key
	return mapping

def dssToOmd(dssFilePath, omdFilePath, RADIUS=0.0002, write_out=True):
	''' Converts the dss file to an OMD, returns the omd tree
	SIDE-EFFECTS: creates the OMD file'''
	# Injecting additional coordinates.
	#TODO: derive sensible RADIUS from lat/lon numbers.
	tree = dssToTree(dssFilePath)
	evil_glm = evilDssTreeToGldTree(tree)
	name_map = _name_to_key(evil_glm)
	print(name_map)
	for ob in evil_glm.values():
		ob_name = ob.get('name','')
		ob_type = ob.get('object','')
		if 'parent' in ob:
			parent_name = ob['parent']
			if ob_type == 'capcontrol':
				cap_name = ob['capacitor']
				cap_id = name_map[cap_name]
				if 'parent' in evil_glm[cap_id]:
					parent_name = evil_glm[cap_id]['parent']
				else:
					parent_name = ob['parent']
			if ob_type == 'energymeter':
				short_parent_name = parent_name.split('.')[1]
				parent_id = name_map[short_parent_name]
				if 'parent' in evil_glm[parent_id]:
					parent_name = evil_glm[parent_id]['parent']
				elif evil_glm[parent_id].get('object','') == 'line':
					from_name = evil_glm[parent_id].get('from', None)
					to_name = evil_glm[parent_id].get('from', None)
					if from_name is not None:
						parent_name = from_name
					elif to_name is not None:
						parent_name = to_name
					else:
						parent_name = ob['parent']
			# get location of parent object.
			parent_loc = name_map[parent_name]
			parent_ob = evil_glm[parent_loc]
			parent_lat = parent_ob.get('latitude', None)
			parent_lon = parent_ob.get('longitude', None)
			# place randomly on circle around parent.
			angle = random.random()*3.14159265*2;
			x = math.cos(angle)*RADIUS;
			y = math.sin(angle)*RADIUS;
			ob['latitude'] = str(float(parent_lat) + x)
			ob['longitude'] = str(float(parent_lon) + y)
	if write_out:
		evilToOmd(evil_glm, omdFilePath)
	return evil_glm

def omdToTree(omdFilePath):
	''' Get a nice opendss tree in memory from an OMD. '''
	omd = json.load(open(omdFilePath))
	evil_tree = omd.get('tree',{})
	dss_tree = evilGldTreeToDssTree(evil_tree)
	return dss_tree

def dss_to_networkx(dssFilePath, tree=None):
	''' Return a networkx directed graph from a dss file. If tree is provided, build graph from that instead of the file. '''
	if tree == None:
		tree = dssToTree(dssFilePath)
	omd = evilDssTreeToGldTree(tree)
	# Gather edges, leave out source and circuit objects
	edges = [(ob['from'],ob['to']) for ob in omd.values() if 'from' in ob and 'to' in ob]
	edges_sub = [
		(ob['parent'],ob['name']) for ob in omd.values()
		if 'name' in ob and 'parent' in ob and ob.get('object') not in ['circuit', 'vsource']
	]
	full_edges = edges + edges_sub
	G = nx.DiGraph(full_edges)
	for ob in omd.values():
		if 'latitude' in ob and 'longitude' in ob:
			G.add_node(ob['name'], pos=(float(ob['longitude']), float(ob['latitude'])))
		else:
			G.add_node(ob['name'])
	return G

def getDssCoordinates(omdFilePath, outFilePath):
	''' Gets a list of location assignments for loads and buses given an omd with valid coordinates '''
	omd = json.load(open(omdFilePath))
	evil_tree = omd.get('tree',{})
	coordinateDict = {}
	for ob in evil_tree.values():
		obType = ob['object']
		obName = ob['name']
		if obType == 'bus' and obName not in coordinateDict.keys():
			print(obType + " --- " + obName)
			latitude = ob['latitude']
			longitude = ob['longitude']
			coordinateDict[obName] = (latitude, longitude)
	with open(outFilePath, "w") as coordinateListFile:
		for bus in coordinateDict.keys():
			busLat = coordinateDict[bus][0]
			busLon = coordinateDict[bus][1]
			lineStr = "setbusxy bus=" + bus + " x=" + busLon + " y=" + busLat + "\n"
			coordinateListFile.write(lineStr)

def _conversionTests():
	# pass
	glmList = set()
	mdbList = set()
	cleanGlmList = set()
	cleanMdbList = set()
	brokenGlmList = {}
	brokenMdbList = {}

	#set to True if you want to test all the glm files, otherwise it will just read the file paths from the previously saved workingGlmList.csv
	shouldTestGlm = False

	curDir = os.getcwd()
	os.chdir('../..')
	omfDir = os.getcwd()

	def fillFileLists():
		for root, dirs, files in os.walk(omfDir):
			for f in files:
				if f.endswith(".glm"):
					glmList.add(os.path.join(root, f))
				if f.endswith(".mdb"):
					mdbList.add(os.path.join(root, f))
		#print("***********glmList = " + ", ".join(glmList))
		#print("***********mdbList = " + ", ".join(mdbList))

	def testAllGlm():
		for f in glmList:
			fPathShort = f
			if f.startswith(omfDir):
				fPathShort = f[len(omfDir):]
			if fPathShort.startswith('/'):
				fPathShort = fPathShort[1:]
			#run gridlabd
			try:
				result = subprocess.run(["gridlabd", f], shell=True, check=True)
				# result = subprocess.run(["gridlabd", f], shell=True, check=True) #cwd=path.get_folder(f)
				cleanGlmList.add(fPathShort)
			except subprocess.CalledProcessError as e:
				# print("Error with ", fPathShort, ": ", e.output)
				brokenGlmList[fPathShort] = e.output
		#save list of working glms to csv file
		with open(pJoin(omfDir, "scratch", "dittoTestOutput", "workingGlmList.csv"),"w") as workingGlmListFile:
			csv_writer = csv.writer(workingGlmListFile)
			for x in cleanGlmList:
				csv_writer.writerow([x])
		#save list of broken glms to csv file
		with open(pJoin(omfDir, "scratch", "dittoTestOutput", "brokenGlmList.csv"),"w") as brokenGlmListFile:
			csv_writer2 = csv.writer(brokenGlmListFile)
			for x in brokenGlmList.keys():
				errorMsg = brokenGlmList[x].replace("\n","\t*\t")
				csv_writer2.writerow([x, errorMsg])
		# print("***********cleanGlmList = " + ", ".join(cleanGlmList))
		# print("***********brokenGlmList = " + ", ".join(brokenGlmList))

	def testAllCyme():
		for f in mdbList:
			#run gridlabd
			fShort = f[len(omfDir):]
			try:
				result = subprocess.run(["", f], shell=True, check=True)
				cleanMdbList.add(fShort)
			except subprocess.CalledProcessError as e:
				brokenMdbList[fShort] = e.output
		# print("***********cleanMdbList = " + ", ".join(cleanMdbList))
		# print("***********brokenMdbList = " + ", ".join(brokenMdbList))
	# all_glm_files = os.system('find ../.. -name *.glm')
	# inputs = get urls for the input files. OMF_GITHUB_URL + extension.
	fillFileLists()
	
	if shouldTestGlm:
		testAllGlm()
	else:
		with open(pJoin(omfDir, "scratch", "dittoTestOutput", "workingGlmList.csv"),"r") as workingGlmListFile:
			#read the names of the working files into cleanGlmList
			csv_reader = csv.reader(workingGlmListFile)
			for row in csv_reader:
				print(row[0])
				cleanGlmList.add(row[0])
		with open(pJoin(omfDir, "scratch", "dittoTestOutput", "brokenGlmList.csv"),"r") as brokenGlmListFile:
			#read the names of the working files into cleanGlmList
			csv_reader2 = csv.reader(brokenGlmListFile)
			for row in csv_reader2:
				filePath = row[0]
				errMsg = row[1]
				brokenGlmList[filePath] = errMsg

	brokenDittoList = {}
	cleanDittoList = {}
	# working_dir = './TEMP_CONV/'
	try:
		os.mkdir(pJoin(omfDir, "scratch", "dittoTestOutput"))
	except FileExistsError:
		print("dittoTestOutput folder already exists!")
		pass
	except:
		print("Error occurred creating dittoTestOutput folder")


	for fname in cleanGlmList:
		fLong = pJoin(omfDir, fname)
		fShort = fname
		if '/' in fname:
			fShort = fname.rsplit('/',1)[1]
		try:
			convFilePath = pJoin(omfDir, "scratch", "dittoTestOutput", fShort + '_conv.dss')
			t0 = time()
			gridLabToDSS(fLong, convFilePath)
			t1 = time()
			cleanDittoList[fname] = {}
			cleanDittoList[fname]["convPath"] = convFilePath
			cleanDittoList[fname]["convTime"] = t1-t0
		except:
			errorMsg = traceback.format_exc()
			brokenDittoList[fname] = {}
			brokenDittoList[fname]["fullPath"] = fLong
			brokenDittoList[fname]["errMsg"] = errorMsg.replace("\n","\t*\t")
			pass

	# TECHNIQUES FOR HANDLING GLM INCLUDES
	# glm_str = open('glm_path.glm').read()
	# if '#include' in glm_str:
	# 	if quick_and_easy_flag:
	# 		pass #skip test, until we can work out includes.
	# 	else:
	# 		include_file = open('path to the include')
	# 		glm_str.replace('#include name.glm', include_file)

	# for key in brokenDittoList.keys():
	# 	print(key + ": " + brokenDittoList[key])

	#create a new file to save the broken ditto runs to
	with open(pJoin(omfDir, "scratch", "dittoTestOutput", "brokenDittoList.csv"),"w") as brokenDittoFile:
		writer = csv.writer(brokenDittoFile)
		# writer.writerows(brokenDittoList.items())
		for fname in brokenDittoList.keys():
			writer.writerow((fname, brokenDittoList[fname]["fullPath"], brokenDittoList[fname]["errMsg"]))

	def createFullReport():
		with open(pJoin(omfDir, "scratch", "dittoTestOutput", "fullDittoReport.csv"),"w") as fullReportFile:
			fieldnames = ['filePath', 'gridlabdResult', 'dittoResult', 'conversionTime', 'originalFileSize', 'convertedFileSize', 'sizeDifference', 'powerflowResutls']
			writer = csv.DictWriter(fullReportFile, fieldnames=fieldnames)

			#write the column headers
			writer.writeheader()
			# add information from broken gridlab-d files
			for x in brokenGlmList.keys():
				writer.writerow({'filePath': x, 'gridlabdResult': brokenGlmList[x], 'dittoResult': 'N/A', 'conversionTime': 'N/A', 'originalFileSize': 'N/A', 'convertedFileSize': 'N/A', 'sizeDifference': 'N/A', 'powerflowResutls': 'N/A'})
			# add information from working gridlab-d files that break in ditto
			for x in brokenDittoList.keys():
				writer.writerow({'filePath': x, 'gridlabdResult': 'SUCCESS', 'dittoResult': brokenDittoList[x]["errMsg"], 'conversionTime': 'N/A', 'originalFileSize': 'N/A', 'convertedFileSize': 'N/A', 'sizeDifference': 'N/A', 'powerflowResutls': 'N/A'})
			# add information from working gridlab-d files that ditto converts
			for x in cleanDittoList.keys():
				# TODO: fill out 'originalFileSize', 'convertedFileSize', 'sizeDifference', 'powerflowResutls'
				writer.writerow({'filePath': x, 'gridlabdResult': 'SUCCESS', 'dittoResult': cleanDittoList[x]["convPath"], 'conversionTime': cleanDittoList[x]["convTime"], 'originalFileSize': 'N/A', 'convertedFileSize': 'N/A', 'sizeDifference': 'N/A', 'powerflowResutls': 'N/A'})

	createFullReport()
	# print(brokenDittoList.keys())
	# zip up all inputs, outputs, exceptions + send to nrel
	# Deprecated tests section
	#dssToGridLab('ieee37.dss', 'Model.glm') # this kind of works
	# gridLabToDSS('ieee13.glm', 'ieee13_conv.dss') # this fails miserably
	#cymeToDss(...) # first need to define function.
	#distNetViz.insert_coordinates(evil_glm)

def _randomTest():
	curDir = os.getcwd()
	os.chdir('../..')
	omfDir = os.getcwd()
	s1 = "/this is a string"
	s2 = "something/file.ext"
	s3 = "/Users/ryanmahoney/omf/omf/someLocation/anotherLocation/file.ext"
	testSet = [s1, s2, s3]
	for f in testSet:
		fPathShort = f
		fName = f
		if f.startswith(omfDir):
			fPathShort = f[len(omfDir):]
		if '/' in fPathShort:
			fName = fPathShort.rsplit('/',1)[1]
		if fPathShort.startswith('/'):
			fPathShort = fPathShort[1:]
		print(f," -> ", fPathShort, " , ", fName)
	with open(pJoin(omfDir, "scratch", "dittoTestOutput", "workingGlmList.csv"),"w") as workingGlmListFile:
		csv_writer = csv.writer(workingGlmListFile)
		for x in testSet:
			csv_writer.writerow([x])

def _dssToOmdTest():
	omfDir = omf.omfDir
	# dssFileName = 'ieee37.clean.dss'
	# dssFilePath = pJoin(curDir, dssFileName)
	dssFileName = 'nreca1824_dwp.dss'
	# dssFileName = 'Master3.dss'
	dssFilePath = pJoin(omfDir, 'static', 'testFiles', dssFileName)
	# dssFilePath = pJoin(omfDir, 'static', 'testFiles', 'Delete', dssFileName)
	# dssCleanLists(dssFilePath)
	# dssFileName = 'Master3_cleanLists.dss'
	# dssFilePath = pJoin(omfDir, 'static', 'testFiles', 'Delete', dssFileName)
	# omdFileName = dssFileName + '.omd'
	omdFileName = dssFileName + '.omd'
	omdFilePath = pJoin(omfDir, 'static', 'testFiles', omdFileName)
	# omdFilePath = pJoin(omfDir, 'static', 'testFiles', 'Delete', omdFileName)
	# omdFilePath = pJoin(omfDir, 'static', 'publicFeeders', omdFileName)
	dssToOmd(dssFilePath, omdFilePath, RADIUS=0.0002, write_out=True)

def _dssCoordTest():
	omfDir = omf.omfDir
	omdFilePath = pJoin(omfDir, "scratch", "MapTestOutput", "iowa240c2_fixed_coords2.clean.omd")
	outFilePath = pJoin(omfDir, "static", "testFiles", "iowa_240", "iowa240_cleanCoords.csv")
	getDssCoordinates(omdFilePath, outFilePath)

def _tests():
	from omf.solvers.opendss import getVoltages, voltageCompare
	import pandas as pd
	FNAMES =  ['ieee37.clean.dss', 'ieee123_solarRamp.clean.dss', 'iowa240.clean.dss', 'ieeeLVTestCase.clean.dss', 'ieee8500-unbal_no_fuses.clean.dss']
	for fname in FNAMES:
		fpath = omf.omfDir + '/solvers/opendss/' + fname
		print('!!!!!!!!!!!!!! ',fpath,' !!!!!!!!!!!!!!')
		# Roundtrip conversion test
		errorLimit = 0.001
		startvolts = getVoltages(fpath, keep_output=False)
		dsstreein = dssToTree(fpath)
		# pp([dict(x) for x in dsstreein]) # DEBUG
		# treeToDss(dsstreein, 'TEST.dss') # DEBUG
		glmtree = evilDssTreeToGldTree(dsstreein)
		#pp(glmtree) #DEBUG
		#distNetViz.viz_mem(glmtree, open_file=True, forceLayout=False)
		dsstreeout = evilGldTreeToDssTree(glmtree)
		outpath = fpath[:-4] + '_roundtrip_test.dss'
		treeToDss(dsstreeout, outpath)
		#...roundtrip a second time to check the output dss syntax
		dsstreein2 = dssToTree(outpath)
		glmtree2 = evilDssTreeToGldTree(dsstreein2)
		distNetViz.viz_mem(glmtree2, open_file=True, forceLayout=False)
		dsstreeout2 = evilGldTreeToDssTree(glmtree2)
		treeToDss(dsstreeout2, outpath)
		endvolts = getVoltages(outpath, keep_output=False)
		os.remove(outpath)
		# percSumm, diffSumm = voltageCompare(startvolts, endvolts, saveascsv=False, with_plots=False)
		# maxPerrM = [percSumm.loc['RMSPE',c] for c in percSumm.columns if c.lower().startswith(' magnitude')]
		# maxPerrM = pd.Series(maxPerrM).max()
		#print(maxPerrM) # DEBUG
		# assert abs(maxPerrM) < errorLimit*100, 'The average percent error in voltage magnitude is %s, which exceeeds the threshold of %s%%.'%(maxPerrM,errorLimit*100)

	#TODO: make parser accept keyless items with new !keyless_n key? Or is this just horrible syntax?
	#TODO: refactor in to well-defined bijections between object types?
	#TODO: a little help on the frontend to hide invalid commands.

if __name__ == '__main__':
	# _tests()
	# _randomTest()
	# _conversionTests()
	_dssToOmdTest()
	#_dssCoordTest()