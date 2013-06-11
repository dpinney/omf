#!/usr/bin/env python

import os, shutil, json

# os.chdir('Study')
# for name in os.listdir('.'):
# 	if name.endswith('.md'):
# 		with open(name,'r') as mdFile, open(name[0:-3] + '.json','r') as jsonFile, open('OUT-' + name[0:-3] + '.json', 'w') as outFile:
# 			md = json.load(mdFile)
# 			data = json.load(jsonFile)
# 			json.dump(dict(md.items()+data.items()),outFile,indent=4)

os.chdir('Study')
for name in os.listdir('.'):
	if name.startswith('OUT-'):
		os.rename(name,name[4:])

# os.chdir('Component')
# for name in os.listdir('.'):
# 	if name.endswith('.json'):
# 		os.rename(name, name[0:-5] + '.md')

# os.chdir('Feeder')
# for name in os.listdir('.'):
# 	if name.endswith('.json'):
# 		os.rename(name, name[0:-5] + '.md')

# os.chdir('Study')
# for name in os.listdir('.'):
# 	if name.endswith('.md.json'):
# 		os.rename(name, name[0:-5])

# import json
# os.chdir('Weather')
# for name in os.listdir('.'):
# 	with open(name,'r') as tmy2File:
# 		data = tmy2File.read()
# 	with open(name[0:-5] + '.md','w') as newFile:
# 		json.dump({'type':'tmy2','tmy2':data}, newFile, indent=4)