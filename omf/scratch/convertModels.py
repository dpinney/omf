import os
from os.path import join as pJoin
import json
import shutil

#paths
workDir = pJoin(os.getcwd()).split("/scratch")[0]
modelDir = pJoin(workDir, "data", "Model")

# traverse users models and rename feeders and convert models
users = os.listdir(modelDir)
for user in users:
	print "=================================="
	userDir = pJoin(modelDir, user)
	print "Converting for",
	print "User: %s"%userDir.split('/')[-1]
	try:
		modelNames = os.listdir(userDir)
		for model in modelNames:
			eachmodelDir = pJoin(userDir, model)
			print "Model: %s"%(eachmodelDir.split('/')[-1])
			try:
				# read input data.
				with open(pJoin(eachmodelDir, "allInputData.json")) as inJson:
					inputData = json.load(inJson)
				with open(pJoin(eachmodelDir, "allOutputData.json")) as outJson:
					outData = json.load(outJson)
				if 'feeder.json' in os.listdir(eachmodelDir):
					# single feeders.
					feederName = inputData.get('feederName')
					try: feederName = feederName.strip("public___")
					except:
						try: feederName = feederName.strip("admin___")
						except: pass
					print "Single-feeder model with:",feederName
					os.rename(pJoin(eachmodelDir,'feeder.json'),pJoin(eachmodelDir, feederName+'.omd'))
					inputData['feederName1'] = feederName
					inputData.pop('feederName',None)
					outData['feederName1'] = feederName
					outData.pop('feederName',None)
					# write back to output.
					with open(pJoin(eachmodelDir,"allInputData.json"),"w") as inputFile:
						json.dump(inputData, inputFile, indent = 4)
					with open(pJoin(eachmodelDir,"allOutputData.json"),"w") as outputFile:
						json.dump(outData, outputFile, indent = 4)
				elif 'feederName' in str(inputData.keys()):
					# multi-feeder models.
					feederNames = [inputData[key] for key in inputData.keys() if 'feederName' in key]
					print "Multi-feeder model with:",feederNames
					for (dirpath, dirnames, filenames) in os.walk(eachmodelDir):
						if dirpath != eachmodelDir:
							for file in filenames:
								if file == 'feeder.json':
									shutil.copyfile(pJoin(dirpath,file),pJoin(eachmodelDir,dirpath.split('/')[-1]+'.omd'))
									for key in inputData.keys():
										if 'feederName' in key:
											feederName = inputData.get(key)
											try: feederName = feederName.strip("public___")
											except:
												try: feederName = feederName.strip("admin___")
												except: pass
											if key != 'feederName':
												inputData[key] = feederName
												outData[key] = feederName
											else:
												inputData['feederName1'] = feederName
												inputData.pop(key,None)
												outData['feederName1'] = feederName
									# write back to output.
									with open(pJoin(eachmodelDir,"allInputData.json"),"w") as inputFile:
										json.dump(inputData, inputFile, indent = 4)
									with open(pJoin(eachmodelDir,"allOutputData.json"),"w") as outputFile:
										json.dump(outData, outputFile, indent = 4)
					print "Successfully converted model."
				else: print "...model ignored."
				print "\n"
			except:
				print "*****Failed.\n"
	except:
		print "*****Failed: couldn't find models."