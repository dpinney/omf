import json, os
from os.path import join as pJoin
import omf
from omf.models import __neoMetaModel__
from omf.models.__neoMetaModel__ import *

good_coords = pJoin(__neoMetaModel__._omfDir,'static','publicFeeders','iowa240c1.clean.dss.omd')
# good_coords = '/Users/dpinney/gdrive/LATERBASE/omf/omf/static/publicFeeders/iowa240c1.clean.dss.omd'
data_working = pJoin(__neoMetaModel__._omfDir,'static','publicFeeders','iowa240c2_workingOnm.clean.dss.omd')
# data_working = '/Users/dpinney/gdrive/LATERBASE/omf/omf/static/publicFeeders/iowa240c2_workingOnm.clean.dss.omd'
with open(good_coords,'r') as good_file:
	with open(data_working,'r') as data_work_file:
		good_coord_omd = json.load(good_file)
		data_work_omd = json.load(data_work_file)
		# print(good_coord_omd)
		fixed_coords = {}
		for key in good_coord_omd['tree']:
			ob = good_coord_omd['tree'][key]
			if 'latitude' in ob and 'longitude' in ob:
				fixed_coords[ob.get('name','NONAME')] = (ob['latitude'], ob['longitude'])
				pass#print(ob.get('name','NONAME'),ob.get('latitude','NOLAT'),ob.get('longitude','NOLON'))
		for key in data_work_omd['tree']:
			ob = data_work_omd['tree'][key]
			if 'latitude' in ob and 'longitude' in ob:
				my_name = ob.get('name','NONAME')
				my_lat = ob.get('latitude','NOLAT')
				my_lon = ob.get('longitude','NOLON')
				if my_name not in fixed_coords:
					del data_work_omd['tree'][key]['latitude']
					del data_work_omd['tree'][key]['longitude']
				else:
					new_lat, new_lon = fixed_coords[my_name]
					data_work_omd['tree'][key]['latitude'] = new_lat
					data_work_omd['tree'][key]['longitude'] = new_lon
				# print(my_name, my_lat, my_lon, fixed_coords.get(my_name,'NOFIX'))
		with open('FIXED_THING.omd','w') as out_file:
			json.dump(data_work_omd, out_file)

from omf.distNetViz import viz

viz('FIXED_THING.omd')