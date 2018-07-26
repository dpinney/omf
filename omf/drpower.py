import omf, os, web, json

def sigh():
	return 'SIGH'

def transmissionConvert(owner, modelName, fileName):
	'First, DRPOWER creates a new transmission model folder.' + \
	'Then it places an .m file in that folder named fileName' + \
	'Then send a request to this route and redirect the user accordingly'
	# Model folder full path.
	modelDir = os.path.join(omf.omfDir, 'data', 'Model', owner, modelName)
	# Remove the existing file.
	existingOmts = [x for x in os.listdir(modelDir) if x.endswith('.omt')]
	for f in existingOmts:
		try:
			os.remove(os.path.join(modelDir,f))
		except:
			pass # Ignore deletion failure.
	# Convert and lay out the new file.
	netJson = omf.network.parse(os.path.join(modelDir, fileName), filePath=True)
	omf.network.layout(netJson)
	with open(os.path.join(modelDir, fileName + '.omt'),'w') as outFile:
		json.dump(netJson, outFile)
	# Rewrite allInputData.json
	with open(os.path.join(modelDir, 'allInputData.json'),'r+') as inFile:
		inData = json.load(inFile)
		inData['networkName1'] = fileName + '.omt'
		inFile.seek(0)
		json.dump(inData,inFile)
		inFile.truncate()
	return 'CONVERTED'

def powerPublish(owner, modelName):
	'Hook to pull data back to DRPOWER main repository.'
	return web.redirect('DRP_PLACEHOLDER_DRP' + '/' + owner + '/' + modelName)

def injectUser(email, passwordHash, modelName):
	'Create a new user and log that user in. Note that hash should be pbkdf2_sha512'
	user = {'username':email, 'password_digest':passwordHash}
	web.flask_login.login_user(web.User(user))
	with open('./data/User/'+ email + '.json','w') as outFile:
		json.dump(user, outFile, indent=4)
	return web.redirect('/network/' + email + '/' + modelName + '/1')

if __name__ == '__main__':
	template_files = ['templates/'+ x  for x in web.safeListdir('templates')]
	model_files = ['models/' + x for x in web.safeListdir('models')]
	# Add routes.
	web.app.add_url_rule('/sigh', 'sigh', view_func=sigh)
	web.app.add_url_rule('/transmissionConvert/<owner>/<modelName>/<fileName>', 'transmissionConvert', view_func=transmissionConvert)
	web.app.add_url_rule('/publishModel/<owner>/<modelName>/', 'powerPublish', methods=['POST'], view_func=powerPublish)
	web.app.add_url_rule('/injectUser/<email>/<passwordHash>/<modelName>/', 'injectUser', view_func=injectUser)
	# def crash(): raise Exception
	# web.app.add_url_rule('/crash','crash',view_func=crash)
	# Remove the bogus old publishModel route.
	allRules = web.app.url_map._rules
	del web.app.url_map._rules_by_endpoint['publishModel']
	for index, rule in enumerate(allRules):
		if rule.endpoint == 'publishModel':
			delIndex = index
	del allRules[delIndex]
	# Start the server.
	web.app.run(
		host='0.0.0.0',
		port=5001,
		threaded=True,
		extra_files=template_files + model_files,
		# debug=True
	)