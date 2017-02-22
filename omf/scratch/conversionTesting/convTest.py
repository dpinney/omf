# Note: While trying to debug, I re-encrypted most of the files. The files in the doNotConvert... folder 
# are now encrypted a different way than the ones in the encryptedFiles folder. Because of this they will not decrypt
import os, json, traceback, shutil, sys
from os.path import join as pJoin
import matplotlib
from matplotlib import pyplot as plt
from cryptography.fernet import Fernet
# OMF Functions
import omf
from solvers import gridlabd

# Paths
_myDir = os.path.dirname(os.path.abspath(__file__))
_cryptoPath = _myDir
sys.path.insert(0,_cryptoPath)

# Key functions.
def genKey(workDir, currUser):
	'''Generate and save encryption key to .key file.'''
	key = Fernet.generate_key()
	with open(pJoin(workDir,currUser+".key"),"w+") as tempFile:
		tempFile.write(key)
def getKey(workDir, currUser):
	'''Read and return a given user's encryption key from path.'''
	try:
		with open (pJoin(workDir, currUser+".key"), "r") as keyFile:
			key = keyFile.read()
		return key
	except:
		return "Couldn't find a key for target:", currUser

# Encryption/Decryption
def encryptData(data, key):
	'''Encrypt and return encrypted data.'''
	cipher_suite = Fernet(key)
	encryptedData = cipher_suite.encrypt(str(data))
	return encryptedData

def decryptData(data, key):
	'''Decrypt and return plaintext data.'''
	cipher_suite = Fernet(key)
	plainText = cipher_suite.decrypt(str(data))
	return plainText

# Convert glm to json.
def gridlabImport(workDir, feederName, glmString):
	''' Function to convert a glm to json. '''
	newFeeder = dict(**omf.feeder.newFeederWireframe)
	newFeeder["tree"] = omf.feeder.parse(glmString, False)
	newFeeder["layoutVars"]["xScale"] = 0
	newFeeder["layoutVars"]["yScale"] = 0
	newFeeder["attachments"] = {}
	with open(pJoin(workDir,feederName+".json"), "w") as outFile:
		json.dump(newFeeder, outFile, indent=4)
	return newFeeder

# MILSOFT WINDMIL TO GRIDLAB TESTS
def milsoftToGridlabTests(files,keepFiles=False):
	openPrefix = './decryptedDataFiles'
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
	# 	testFiles = [('INEC-RENOIR.std','INEC.seq'), ('INEC-GRAHAM.std','INEC.seq'),
	#   ('Olin-Barre.std','Olin.seq'), ('Olin-Brown.std','Olin.seq'),
	#  	('ABEC-FRANK.std','ABEC.seq'), ('ABEC-COLUMBIA.std','ABEC.seq'),('OMF_Norfork1.std', 'OMF_Norfork1.seq')]
	testFiles = files
	testAttachments = {'schedules.glm':open(pJoin(openPrefix,'schedules.glm'),'r').read(), 'climate.tmy2':open(pJoin(openPrefix,'AK-ANCHORAGE.tmy2'),'r').read()}
	for stdString, seqString in testFiles:
		try:
			# Convert the std+seq.
			with open(pJoin(openPrefix,stdString),'r') as stdFile, open(pJoin(openPrefix,seqString),'r') as seqFile:
				outGlm,x,y = convert(stdFile.read(),seqFile.read())
			with open(outPrefix + stdString.replace('.std','.glm'),'w') as outFile:
				outFile.write(feeder.sortedWrite(outGlm))
			print 'WROTE GLM FOR', stdString
			with open(pJoin(_myDir,'convResults.txt'),'a') as resultsFile:
				resultsFile.write('WROTE GLM FOR ' + stdString + "\n")
			try:
				# Draw the GLM.
				myGraph = feeder.treeToNxGraph(outGlm)
				feeder.latLonNxGraph(myGraph, neatoLayout=False)
				plt.savefig(outPrefix + stdString.replace('.std','.png'))
				print 'DREW GLM OF', stdString
				with open(pJoin(_myDir,'convResults.txt'),'a') as resultsFile:
					resultsFile.write('DREW GLM FOR ' + stdString + "\n")
			except:
				exceptionCount += 1
				print 'FAILED DRAWING', stdString
				with open(pJoin(_myDir,'convResults.txt'),'a') as resultsFile:
					resultsFile.write('FAILED DRAWING ' + stdString + "\n")
			try:
				# Run powerflow on the GLM. HACK:blank attachments for now.
				output = gridlabd.runInFilesystem(outGlm, attachments=testAttachments, keepFiles=False)
				with open(outPrefix + stdString.replace('.std','.json'),'a') as outFile:
					json.dump(output, outFile, indent=4)
				print 'RAN GRIDLAB ON', stdString
				with open(pJoin(_myDir,'convResults.txt'),'a') as resultsFile:
					resultsFile.write('RAN GRIDLAB ON ' + stdString + "\n")
			except:
				exceptionCount += 1
				print 'POWERFLOW FAILED', stdString
				with open(pJoin(_myDir,'convResults.txt'),'a') as resultsFile:
					resultsFile.write('POWERFLOW FAILED ' + stdString + "\n")
		except:
			print 'FAILED CONVERTING', stdString
			with open(pJoin(_myDir,'convResults.txt'),'a') as resultsFile:
					resultsFile.write('FAILED CONVERTING ' + stdString + "\n")
			exceptionCount += 1
			traceback.print_exc()
	if not keepFiles:
		shutil.rmtree(outPrefix)
	return exceptionCount

def _tests():
	user = 'convTest'
	key = getKey(_cryptoPath,user)
	encryptedFilesFolder = pJoin(_cryptoPath,"encryptedFiles")

	# Delete decrypted folder if it exists
	if(os.path.isdir(pJoin(_cryptoPath,"decryptedDataFiles"))):
		shutil.rmtree(pJoin(_cryptoPath,"decryptedDataFiles"))

	# Remake decrypted folder
	if not (os.path.isdir(pJoin(_cryptoPath,"decryptedDataFiles"))):
		os.makedirs(pJoin(_cryptoPath,"decryptedDataFiles"))
	decryptedDataFolder = pJoin(_cryptoPath,"decryptedDataFiles")

	# Decrypts encrypted Files and writes to decrypted data folder
	for file in os.listdir(encryptedFilesFolder):
		# HACK: Was running into issues with a hidded .DS_Store file in my directories
		if not file.startswith('.'):
			with open(pJoin(encryptedFilesFolder,str(file)),'r') as r:
				r = r.read()
			fileName = str(file)[10:]
			decryptedData = decryptData(r,key)
			with open(pJoin(decryptedDataFolder,fileName),"w+") as f:
				f.write(decryptedData)

	# Creating [[.std,.seq],[.std,.seq],[.stq,.seq],...] structure for testing functions
	# This is a HACK, could use some help here, flatten/zip functions?
	seqFilenames = []
	groupedFiles = []
	for file in os.listdir(decryptedDataFolder):
		if str(file).endswith('.seq'):
			filename = file[:-4]
			seqFilenames.append(filename)
	for file in seqFilenames:
		group = []
		for f in os.listdir(decryptedDataFolder):
			if str(f).startswith(file):
				group.append(f)
		groupedFiles.append(group)
	arrays = []
	for group in groupedFiles:
		if len(group)>2:
			for item in group:
				array = []
				if item.endswith('.std'):
					array.append(item)
					for item in group:
						if item.endswith('.seq'):
							array.append(item)
							arrays.append(array)
		else:
			arrays.append(group)

	# Runs milsoft tests on seq std files and then deletes results and decrypted files
	milsoftToGridlabTests(arrays)
	if(os.path.isdir('./milToGridlabTests/')):
		shutil.rmtree('./milToGridlabTests/')
	if(os.path.isdir(decryptedDataFolder)):
		shutil.rmtree(decryptedDataFolder)
	print "finished"
if __name__ == "__main__":
	_tests()
# user = 'convTest'
# key = getKey(_cryptoPath,user)
# encryptedFilesFolder = pJoin(_cryptoPath,"encryptedFiles")
# for file in os.listdir("./needEncryption/"):
# 	fileName = "Encrypted_"+str(file)
# 	with open(pJoin("./needEncryption/",str(file)),'r') as r:
# 				r = r.read()
# 	encryptedData = encryptData(r,key)
# 	with open(pJoin(encryptedFilesFolder,fileName),"w+") as f:
# 		f.write(encryptedData)

