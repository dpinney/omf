# Prereq: `pip install 'git+https://github.com/NREL/ditto.git@master#egg=ditto[all]'`
import os
import sys
import json
import warnings
from ditto.store import Store
from ditto.readers.opendss.read import Reader as dReader
from ditto.writers.opendss.write import Writer as dWriter
from ditto.readers.gridlabd.read import Reader as gReader
from ditto.writers.gridlabd.write import Writer as gWriter
from collections import OrderedDict
from omf import feeder, distNetViz

def gridLabToDSS(inFilePath, outFilePath):
	''' Convert gridlab file to dss. ''' 
	model = Store()
	# HACK: the gridlab reader can't handle brace syntax that ditto itself writes...
	# command = 'sed -i -E "s/{/ {/" ' + inFilePath
	# os.system(command)
	gld_reader = gReader(input_file = inFilePath)
	gld_reader.parse(model)
	model.set_names()
	dss_writer = dWriter(output_path=".")
	# TODO: no way to specify output filename, so move and rename.
	dss_writer.write(model)

def dssToGridLab(inFilePath, outFilePath, busCoords=None):
	''' Convert dss file to gridlab. '''
	model = Store()
	#TODO: do something about busCoords: 
	dss_reader = dReader(master_file = inFilePath)
	dss_reader.parse(model)
	model.set_names()
	glm_writer = gWriter(output_path=".")
	# TODO: no way to specify output filename, so move and rename.
	glm_writer.write(model)

def dssToTree(pathToDss):
	''' Convert a .dss file to an in-memory, OMF-compatible "tree" object.
	Note that we only support a VERY specifically-formatted DSS file.'''
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
	for i, line in contents.items():
		jpos = 0
		try:
			#HACK: only support white space separation of attributes.
			contents[i] = line.split()
			# HACK: only support = assignment of values.
			from collections import OrderedDict 
			ob = OrderedDict() 
			ob['!CMD'] = contents[i][0]
			if len(contents[i]) > 1:
				for j in range(1, len(contents[i])):
					jpos = j
					k,v = contents[i][j].split('=')
					ob[k] = v
			contents[i] = ob
		except:
			raise Exception(f'Error encountered in group (space delimited) #{jpos+1} of line {i + 1}: {line}')
	# Print
	# for line in contents:
	# 	print line
	contents = contents.values()
	return contents

def treeToDss(treeObject, outputPath):
	outFile = open(outputPath, 'w')
	for ob in treeObject:
		line = ob['!CMD']
		for key in ob:
			if key not in ['!CMD']:
				line = f'{line} {key}={ob[key]}'
		outFile.write(line + '\n')
	outFile.close()

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
				"object": "node",
				"name": ob['bus'],
				"latitude": ob['y'],
				"longitude": ob['x']
			}
			bus_with_coords.append(ob['bus'])
		elif ob['!CMD'] == 'new':
			obtype, name = ob['object'].split('.')
			if 'bus1' in ob and 'bus2' in ob:
				# line-like object.
				# strip the weird dot notation stuff via find.
				fro = ob['bus1'].split('.')[0]
				to = ob['bus2'].split('.')[0]
				gldTree[str(g_id)] = {
					"object": obtype,
					"name": name,
					"from": fro,
					"to": to
				}
				bus_names.extend([fro, to])
				_extend_with_exc(ob, gldTree[str(g_id)], ['object','bus1','bus2','!CMD'])
			elif 'buses' in ob:
				#transformer-like object.
				b1, b2 = ob['buses'].replace('(','').replace(')','').split(',')
				fro = b1.split('.')[0]
				to = b2.split('.')[0]
				gldTree[str(g_id)] = {
					"object": obtype,
					"name": name,
					"from": fro,
					"to": to
				}
				bus_names.extend([fro, to])
				_extend_with_exc(ob, gldTree[str(g_id)], ['object','buses','!CMD'])
			elif 'bus' in ob:
				#load-like object.
				bus_root = ob['bus'].split('.')[0]
				gldTree[str(g_id)] = {
					"object": obtype,
					"name": name,
					"parent": ob['bus'].split('.')[0]
				}
				bus_names.append(bus_root)
				_extend_with_exc(ob, gldTree[str(g_id)], ['object','bus','!CMD'])
			elif 'bus1' in ob and 'bus2' not in ob:
				#load-like object, alternate syntax
				bus_root = ob['bus1'].split('.')[0]
				gldTree[str(g_id)] = {
					"object": obtype,
					"name": name,
					"parent": bus_root
				}
				bus_names.append(bus_root)
				_extend_with_exc(ob, gldTree[str(g_id)], ['object','bus1','!CMD'])
			else:
				#config-like object.
				gldTree[str(g_id)] = {
					"object": obtype,
					"name": name
				}
				_extend_with_exc(ob, gldTree[str(g_id)], ['object','!CMD'])
		elif ob['!CMD'] not in ['new', 'setbusxy']:
			#command-like objects.
			gldTree[str(g_id)] = {
				"object": "!CMD",
				"name": ob['!CMD']
			}
			_extend_with_exc(ob, gldTree[str(g_id)], ['!CMD'])
		else:
			warnings.warn(f'Ignored {ob}')
		g_id += 1
	# Warn on buses with no coords.
	no_coord_buses = set(bus_names) - set(bus_with_coords)
	if len(no_coord_buses) != 0:
		warnings.warn(f'Buses without coordintates:{no_coord_buses}')
	return gldTree

def evilGldTreeToDssTree(evil_gld_tree):
	''' Inverse frontend to DSS converter. Still evil. '''
	dssTree = []
	# Put objects in order.
	all_objs = evil_gld_tree.items()
	objs_in_order = [y[1] for y in sorted(all_objs, key=lambda x:int(x[0]))]
	# Process each object.
	for ob in objs_in_order:
		if ob.get('object') == 'node':
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
				'object': 'line.' + ob['name'],
				'bus1': ob['from'],
				'bus2': ob['to'],
			}
			_extend_with_exc(ob, new_ob, ['!CMD','from','to','name','object','latitude','longitude'])
			dssTree.append(new_ob)
		elif ob.get('object') == 'transformer':
			new_ob = {
				'!CMD': 'new',
				'object': 'transformer.' + ob['name'],
				'buses': f'({ob["from"]},{ob["to"]})'
			}
			_extend_with_exc(ob, new_ob, ['!CMD','from','to','name','object','latitude','longitude'])
			dssTree.append(new_ob)
		elif 'parent' in ob:
			new_ob = {
				'!CMD': 'new',
				'object': ob['object'] + '.' + ob['name'],
				'bus': ob['parent'] 
			}
			_extend_with_exc(ob, new_ob, ['parent','name','object','latitude','longitude'])
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
			warnings.warn(f'Unprocessed object: {ob}')
	return dssTree

def evilToOmd(evilTree, outPath):
	omdStruct = dict(feeder.newFeederWireframe)
	omdStruct['syntax'] = 'DSS'
	omdStruct['tree'] = evilTree
	with open(outPath, 'w') as outFile:
		json.dump(omdStruct, outFile, indent=4)

if __name__ == '__main__':
	tree = dssToTree('ieee37_ours.dss')
	# treeToDss(tree, 'ieee37p.dss')
	# dssToMem('ieee37.dss')
	# dssToGridLab('ieee37.dss', 'Model.glm') # this kind of works
	# gridLabToDSS('ieee37_fixed.glm', 'ieee37_conv.dss') # this fails miserably
	from pprint import pprint as pp
	evil_glm = evilDssTreeToGldTree(tree)
	# pp(evil_glm)
	distNetViz.viz_mem(evil_glm, open_file=True, forceLayout=True)
	distNetViz.insert_coordinates(evil_glm)
	# evilToOmd(evil_glm, 'ieee37.dss.omd')
	# evil_dss = evilGldTreeToDssTree(evil_glm)
	# pp(evil_dss)
	# treeToDss(evil_dss, 'HACKZ.dss')
	#TODO: make parser accept keyless items with new !keyless_n key? Or is this just horrible syntax?
	#TODO: define .dsc format and write syntax guide.
	#TODO: what to do about transformers with invalid bus setting with the duplicate keys? Probably ignore.
	#TODO: where to save the x.1.2.3 bus connectivity info?
	#TODO: refactor in to well-defined bijections between object types?
	#TODO: a little help on the frontend to hide invalid commands.