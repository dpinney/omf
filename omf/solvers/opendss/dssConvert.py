# Prereq: `pip install 'git+https://github.com/NREL/ditto.git@master#egg=ditto[all]'`
import os
import sys
import json
import warnings
try:
	from ditto.store import Store
	from ditto.readers.opendss.read import Reader as dReader
	from ditto.writers.opendss.write import Writer as dWriter
	from ditto.readers.gridlabd.read import Reader as gReader
	from ditto.writers.gridlabd.write import Writer as gWriter
except:
	warnings.warn('nrel ditto not installed. opendss conversion disabled.')
from collections import OrderedDict
from omf import feeder, distNetViz
from pprint import pprint as pp

def gridLabToDSS(inFilePath, outFilePath):
	''' Convert gridlab file to dss. ''' 
	#TODO: delete because obsolete?
	model = Store()
	# HACK: the gridlab reader can't handle brace syntax that ditto itself writes...
	# command = 'sed -i -E "s/{/ {/" ' + inFilePath
	# os.system(command)
	gld_reader = gReader(input_file = inFilePath)
	gld_reader.parse(model)
	model.set_names()
	dss_writer = dWriter(output_path='.')
	# TODO: no way to specify output filename, so move and rename.
	dss_writer.write(model)

def dssToGridLab(inFilePath, outFilePath, busCoords=None):
	''' Convert dss file to gridlab. '''
	#TODO: delete because obsolete?
	model = Store()
	#TODO: do something about busCoords: 
	dss_reader = dReader(master_file = inFilePath)
	dss_reader.parse(model)
	model.set_names()
	glm_writer = gWriter(output_path='.')
	# TODO: no way to specify output filename, so move and rename.
	glm_writer.write(model)

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
			raise Exception(f"Error encountered in group (space delimited) #{jpos+1} of line {i + 1}: {line}")
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

def _dssToTree_dssdirect(fpath):
	'''Do not use this function other than to evaluate the accuracy of opendssdirect.py. 
	After reviewing the file output at the end of this function, it is apparent that 
	opendssdirect does not handle the three-winding/repeating key object property 
	definition syntax. Because of this, it was decided that we should pursue a custom 
	parser after all, roundtripping the user-input circuit definition file through OpenDSS 
	to standardize it before parsing.'''
	# import circuit via opendssdirect
	import opendssdirect as dss
	runDssCommand('Redirect ' + fpath)
	runDssCommand('Solve')
	tree = [] # list of dictionaries
	tree.extend(_dfToListOfDicts(dss.utils.capacitors_to_dataframe(),'Capacitor'))
	tree.extend(_dfToListOfDicts(dss.utils.fuses_to_dataframe(), 'Fuse'))
	tree.extend(_dfToListOfDicts(dss.utils.generators_to_dataframe(), 'Generator'))
	tree.extend(_dfToListOfDicts(dss.utils.isource_to_dataframe(), 'ISource'))
	tree.extend(_dfToListOfDicts(dss.utils.lines_to_dataframe(), 'Line'))
	tree.extend(_dfToListOfDicts(dss.utils.loads_to_dataframe(), 'Load'))
	tree.extend(_dfToListOfDicts(dss.utils.loadshape_to_dataframe(), 'LoadShape'))
	tree.extend(_dfToListOfDicts(dss.utils.meters_to_dataframe(), 'Meter'))
	tree.extend(_dfToListOfDicts(dss.utils.monitors_to_dataframe(), 'Monitor'))
	tree.extend(_dfToListOfDicts(dss.utils.pvsystems_to_dataframe(), 'PvSystem'))
	tree.extend(_dfToListOfDicts(dss.utils.reclosers_to_dataframe(), 'Recloser'))
	tree.extend(_dfToListOfDicts(dss.utils.regcontrols_to_dataframe(), 'RegControl'))
	tree.extend(_dfToListOfDicts(dss.utils.relays_to_dataframe(), 'Relay'))
	tree.extend(_dfToListOfDicts(dss.utils.sensors_to_dataframe(), 'Sensor'))
	tree.extend(_dfToListOfDicts(dss.utils.transformers_to_dataframe(), 'Transformer'))
	tree.extend(_dfToListOfDicts(dss.utils.vsources_to_dataframe(), 'VSource'))
	tree.extend(_dfToListOfDicts(dss.utils.xycurves_to_dataframe(), 'XyCurve'))
	
	## One way of getting all the circuit elements....
	# Add the connections (there is not a way I can see to get this info the pandas way...can we ask someone? Do it the other way)
	with open('dssTreeRepresentation_direct.csv', 'w') as outFile:
		for i,objd in enumerate(tree):
			dss.Circuit.SetActiveElement(objd['Object'])
			objd['Cnxns'] = dss.CktElement.BusNames()
			outFile.write(str(i) + '\n')
			for k,v in objd.items():
					outFile.write(',' + str(k) + ',' + str(v) + '\n')
	
	## A second way of getting all the circuit elements....
		## Add the connections (there is not a way I can see to get this info the pandas way...can we ask someone? Do it the other way)
		#allelms = dss.Circuit.AllElementNames()
		#for elm in allelms:
			#dss.Circuit.SetActiveElement(elm)
			## Get variable keys and values (not sure if these matter...)
			#nms = dss.CktElement.AllVariableNames()
			#vls = dss.CktElement.AllVariableValues()
			#elm_dict = dict(zip(nms,vls))
			#elm_dict_vrbls = dict(zip(nms,vls))
			## Get property keys
			#prp_keys = dss.CktElement.AllPropertyNames()
			## Loop to get property values
			#for item in dss.utils.Iterator(prp_keys):
				#prp_keys.#how to read the property of the active element?
			#elm_dict = elm_dict_vrbls.update(prps)
			## Add busnames
			#elm_dict['cnxns'] = dss.CktElement.BusNames()
			#tree.append(elm_dict)
		#allNodes = dss.Circuit.AllNodeNames()
		#allbuses = dss.Circuit.AllBusNames()
		#tree.append(allNodes)
		## Get the buses
		#for node in allNodes:
			#pass
		#for bus in allBuses:
			#dss.Circuit.SetActiveBus(node)
			#cnxns = dss.Bus.LineList().append(dss.Bus.LoadList())
	return tree

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
				gldTree[str(g_id)] = {
					'object': obtype,
					'name': name,
					'parent': cobtype + '.' + cobname,
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
			warnings.warn(f"Unprocessed object: {ob}")
	return dssTree

def evilToOmd(evilTree, outPath):
	omdStruct = dict(feeder.newFeederWireframe)
	omdStruct['syntax'] = 'DSS'
	omdStruct['tree'] = evilTree
	with open(outPath, 'w') as outFile:
		json.dump(omdStruct, outFile, indent=4)

def _createAndCompareTestFile(inFile, userOutFile=''):
	'''Input: the name of the file to be prepared for OMF consumption and perform subsequent checks (import to memory
	and voltage comparison). Provide a second filename via userOutFile to bypass file manipulation and perform only the 
	subsequent checks.'''

	outFile = userOutFile if userOutFile!='' else _dssFilePrep(inFile)
	tree1 = dssToTree(outFile) # check that it can be parsed into a dssTree.
	from omf.solvers.opendss import getVoltages, voltageCompare
	involts = getVoltages(inFile, keep_output=False)
	outvolts = getVoltages(outFile, keep_output=False)
	resFile = 'voltsCompare__' + os.path.split(inFile)[1][:-4] + '___' + os.path.split(outFile)[1][:-4] + '.csv'
	percSumm, diffSumm = voltageCompare(involts, outvolts, keep_output=True)
	return 

def _conversionTests():
	pass
	# Deprecated tests section
	#dssToGridLab('ieee37.dss', 'Model.glm') # this kind of works
	#gridLabToDSS('ieee37_fixed.glm', 'ieee37_conv.dss') # this fails miserably
	#cymeToDss(...) # first need to define function.
	#distNetViz.insert_coordinates(evil_glm)

def _tests():
	from omf.solvers.opendss import getVoltages, voltageCompare
	import pandas as pd
	FNAMES =  ['ieee37.clean.dss', 'ieee123_solarRamp.clean.dss', 'iowa240.clean.dss', 'ieeeLVTestCase.clean.dss', 'ieee8500-unbal_no_fuses.clean.dss']
	
	for fname in FNAMES:
		print('!!!!!!!!!!!!!! ',fname,' !!!!!!!!!!!!!!')
		# Roundtrip conversion test
		errorLimit = 0.001
		startvolts = getVoltages(fname, keep_output=False)
		dsstreein = dssToTree(fname)
		# pp([dict(x) for x in dsstreein]) # DEBUG
		# treeToDss(dsstreein, 'TEST.dss') # DEBUG
		glmtree = evilDssTreeToGldTree(dsstreein)
		#pp(glmtree) #DEBUG
		#distNetViz.viz_mem(glmtree, open_file=True, forceLayout=False)
		dsstreeout = evilGldTreeToDssTree(glmtree)
		outpath = fname[:-4] + '_roundtrip_test.dss'
		treeToDss(dsstreeout, outpath)
		#...roundtrip a second time to check the output dss syntax
		dsstreein2 = dssToTree(outpath)
		glmtree2 = evilDssTreeToGldTree(dsstreein2)
		distNetViz.viz_mem(glmtree2, open_file=True, forceLayout=False)
		dsstreeout2 = evilGldTreeToDssTree(glmtree2)
		treeToDss(dsstreeout2, outpath)
		endvolts = getVoltages(outpath, keep_output=False)
		os.remove(outpath)
		percSumm, diffSumm = voltageCompare(startvolts, endvolts, saveascsv=False, with_plots=False)
		maxPerrM = [percSumm.loc['RMSPE',c] for c in percSumm.columns if c.lower().startswith(' magnitude')]
		maxPerrM = pd.Series(maxPerrM).max()
		#print(maxPerrM) # DEBUG
		assert abs(maxPerrM) < errorLimit*100, 'The average percent error in voltage magnitude is %s, which exceeeds the threshold of %s%%.'%(maxPerrM,errorLimit*100)

	#TODO: make parser accept keyless items with new !keyless_n key? Or is this just horrible syntax?
	#TODO: refactor in to well-defined bijections between object types?
	#TODO: a little help on the frontend to hide invalid commands.

if __name__ == '__main__':
	_tests()