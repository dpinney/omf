#  # CYME TO GRIDLAB TESTS
# def cymeToGridlabTests(keepFiles=True):
# 	import os, json, traceback, shutil
# 	from omf.solvers import gridlabd
# 	from matplotlib import pyplot as plt
# 	import feeder
# 	from cymeToGridlab import convertCymeModel
# 	exceptionCount = 0       
# 	try:
# 		db_network = os.path.abspath('../uploads/IEEE13.mdb')
# 		db_equipment = os.path.abspath('../uploads/IEEE13.mdb')
# 		# db_network = "IEEE13.mdb"
# 		# db_equipment = "IEEE13.mdb"
# 		id_feeder = '650'
# 		conductors = os.path.abspath('./scratch/uploads/conductor_data.csv')
# 		#cyme_base, x, y = convertCymeModel(db_network, db_equipment, id_feeder, conductors)
# 		cyme_base, x, y = convertCymeModel(db_network, db_equipment, test=True, type=1, feeder_id='650')    
# 		glmString = feeder.sortedWrite(cyme_base)
# 		gfile = open("./scratch/uploads/IEEE13.glm", 'w')
# 		gfile.write(glmString)
# 		gfile.close()
# 		print 'WROTE GLM FOR'
# 		outPrefix = './scratch/cymeToGridlabTests/'          
# 		try:
# 			os.mkdir(outPrefix)
# 		except:
# 			pass # Directory already there.     
# 		'''Attempt to graph'''      
# 		try:
# 			# Draw the GLM.
# 			myGraph = feeder.treeToNxGraph(cyme_base)
# 			feeder.latLonNxGraph(myGraph, neatoLayout=False)
# 			plt.savefig(outPrefix + "IEEE13.png")
# 			print 'DREW GLM OF'
# 		except:
# 			exceptionCount += 1
# 			print 'FAILED DRAWING'
# 		try:
# 			# Run powerflow on the GLM.
# 			output = gridlabd.runInFilesystem(glmString, keepFiles=False)
# 			with open(outPrefix + "IEEE.JSON",'w') as outFile:
# 				json.dump(output, outFile, indent=4)
# 			print 'RAN GRIDLAB ON\n'                 
# 		except:
# 			exceptionCount += 1
# 			print 'POWERFLOW FAILED'
# 	except:
# 		print 'FAILED CONVERTING'
# 		exceptionCount += 1
# 		traceback.print_exc()
# 	if not keepFiles:
# 		shutil.rmtree(outPrefix)
	# return exceptionCount   
# MILSOFT WINDMIL TO GRIDLAB TESTS
def milsoftToGridlabTests(keepFiles=False):
	openPrefix = '../uploads/'
	outPrefix = './milToGridlabTests/'
	import os, json, traceback, shutil
	from omf.solvers import gridlabd
	from matplotlib import pyplot as plt
	from milToGridlab import convert
	import omf.feeder as feeder
	try:
		os.mkdir(outPrefix)
	except:
		pass # Directory already there.
	exceptionCount = 0
	# testFiles = [('INEC-RENOIR.std','INEC.seq'), ('INEC-GRAHAM.std','INEC.seq'),
	#   ('Olin-Barre.std','Olin.seq'), ('Olin-Brown.std','Olin.seq'),
	#   ('ABEC-FRANK.std','ABEC.seq'), ('ABEC-COLUMBIA.std','ABEC.seq'),('OMF_Norfork1.std', 'OMF_Norfork1.seq')]
	testFiles = [('Olin-Brown.std', 'Olin.seq')]
	testAttachments = {'schedules.glm':''}
	# testAttachments = {'schedules.glm':'', 'climate.tmy2':open('./data/Climate/KY-LEXINGTON.tmy2','r').read()}
	for stdString, seqString in testFiles:
		try:
			# Convert the std+seq.
			with open(openPrefix + stdString,'r') as stdFile, open(openPrefix + seqString,'r') as seqFile:
				outGlm,x,y = convert(stdFile.read(),seqFile.read())
			with open(outPrefix + stdString.replace('.std','.glm'),'w') as outFile:
				outFile.write(feeder.sortedWrite(outGlm))
			print 'WROTE GLM FOR', stdString
			try:
				# Draw the GLM.
				myGraph = feeder.treeToNxGraph(outGlm)
				feeder.latLonNxGraph(myGraph, neatoLayout=False)
				plt.savefig(outPrefix + stdString.replace('.std','.png'))
				print 'DREW GLM OF', stdString
			except:
				exceptionCount += 1
				print 'FAILED DRAWING', stdString
			try:
				# Run powerflow on the GLM. HACK:blank attachments for now.
				output = gridlabd.runInFilesystem(outGlm, attachments=testAttachments, keepFiles=False)
				with open(outPrefix + stdString.replace('.std','.json'),'w') as outFile:
					json.dump(output, outFile, indent=4)
				print 'RAN GRIDLAB ON', stdString
			except:
				exceptionCount += 1
				print 'POWERFLOW FAILED', stdString
		except:
			print 'FAILED CONVERTING', stdString
			exceptionCount += 1
			traceback.print_exc()
	if not keepFiles:
		shutil.rmtree(outPrefix)
	return exceptionCount
milsoftToGridlabTests()
# cymeToGridlabTests()
# MORE CYME TO GRIDLAB TESTS, FROM testPEC.py
# import sys, os
# sys.path.append('../../')
# from pathlib import Path
# from cymeToGridlab import *
# db_network = os.path.abspath('../uploads/IEEE13.mdb')
# db_equipment = os.path.abspath('../uploads/IEEE13.mdb')
# def moreCymetoGridlabTests(Network, Equipment, keepFiles=True):
# 	import os, json, traceback, shutil
# 	from omf.solvers import gridlabd
# 	from matplotlib import pyplot as plt
# 	import omf.feeder
# 	from cymeToGridlab import convertCymeModel
# 	exceptionCount = 0       
# 	try:
# 		#db_network = os.path.abspath('./scratch/uploads/IEEE13.mdb')
# 		#db_equipment = os.path.abspath('./scratch/uploads/IEEE13.mdb')
# 		prefix = ""
# 		db_network = Network
# 		db_equipment = Equipment
# 		id_feeder = '650'
# 		conductors = prefix + "conductor_data.csv"
# 		#print "dbnet", db_network
# 		#print "eqnet", db_equipment               
# 		#print "conductors", conductors
# 		#cyme_base, x, y = convertCymeModel(db_network, db_equipment, id_feeder, conductors)
# 		cyme_base, x, y = convertCymeModel(str(db_network), str(db_equipment), test=True, type=2, feeder_id='CV160')    
# 		feeder.attachRecorders(cyme_base, "TriplexLosses", None, None)
# 		feeder.attachRecorders(cyme_base, "TransformerLosses", None, None)
# 		glmString = feeder.sortedWrite(cyme_base)
# 		feederglm = "C:\Users\Asus\Documents\GitHub\omf\omf\scratch\uploads\PEC.glm"
# 		#print "feeederglm", feederglm
# 		gfile = open(feederglm, 'w')
# 		gfile.write(glmString)
# 		gfile.close()
# 		#print 'WROTE GLM FOR'
# 		outPrefix = "C:\Users\Asus\Documents\GitHub\omf\omf\scratch\cymeToGridlabTests\\"          
# 		try:
# 			os.mkdir(outPrefix)
# 		except:
# 			pass # Directory already there.     
# 		'''Attempt to graph'''      
# 		try:
# 			# Draw the GLM.
# 			print "trying to graph"
# 			myGraph = feeder.treeToNxGraph(cyme_base)
# 			feeder.latLonNxGraph(myGraph, neatoLayout=False)
# 			plt.savefig(outPrefix + "PEC.png")
# 			print "outprefix", outPrefix + "PEC.png"
# 			print 'DREW GLM OF'
# 		except:
# 			exceptionCount += 1
# 			print 'FAILED DRAWING'
# 		try:
# 			# Run powerflow on the GLM.
# 			output = gridlabd.runInFilesystem(glmString, keepFiles=False)
# 			with open(outPrefix + "PEC.JSON",'w') as outFile:
# 				json.dump(output, outFile, indent=4)
# 			print 'RAN GRIDLAB ON\n'                 
# 		except:
# 			exceptionCount += 1
# 			print 'POWERFLOW FAILED'
# 	except:
# 		print 'FAILED CONVERTING'
# 		exceptionCount += 1
# 		traceback.print_exc()
# 	if not keepFiles:
# 		shutil.rmtree(outPrefix)
# 	return exceptionCount

# moreCymetoGridlabTests(db_network,db_equipment)    
	# '''db_network = os.path.abspath('./scratch/uploads/PasoRobles11cymsectiondevice[device]['phases']08.mdb')
	# db_equipment = os.path.abspath('./scratch/uploads/PasoRobles1108.mdb')
	# id_feeder = '182611108'
	# conductors = os.path.abspath('./scratch/uploads/conductor_data.csv')
	# cyme_base, x, y = convertCymeModel(db_network, db_equipment, id_feeder, conductors)
	# glmString = feeder.sortedWrite(cyme_base)
	# gfile = open("./scratch/uploads/PR1108Conversion.glm", 'w')
	# gfile.write(glmString)
	# gfile.close()'''
