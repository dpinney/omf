'''Contains functions used for cryptography.
'''
import os, json, traceback, shutil
from os.path import join as pJoin
import matplotlib
from matplotlib import pyplot as plt
from cryptography.fernet import Fernet
# OMF Functions
import omf
from solvers import gridlabd

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

# Tests.
def _tests(makeKey=False, runGridlabD=True, showGDLABResults=False, cleanUp=True):
	'''Get and encrypt a .std/.seq files to a .json. cleanUp removes the unencrypted .glm and .json.
	'''
	# Inputs.
	user = "UCS"
	workDir = pJoin(os.getcwd())
	try: os.mkdir(pJoin(os.getcwd(),'encryptedFiles'))
	except: pass
	if makeKey:
		genKey(workDir, user)
		print "Made a new key for user:", user
	key = getKey(workDir, user)
	print "Read key for user:", user
	# Read circuit files and convert to json, encrypting each step.
	exceptionCount = 0
	testAttachments = {'inFiles/schedules.glm':'', 'climate.tmy2':open('inFiles/AK-ANCHORAGE.tmy2','r').read()}
	testFiles = [('INEC-RENOIR.std','INEC.seq'), ('INEC-GRAHAM.std','INEC.seq'), ('Olin-Barre.std','Olin.seq'), ('Olin-Brown.std','Olin.seq'),('ABEC-FRANK.std','ABEC.seq'), ('ABEC-COLUMBIA.std','ABEC.seq')]
	# testFiles = [('OMF_Norfork1.std','OMF_Norfork1.seq')] # This takes a long time, include in the test if you wish.
	try:
		for stdString, seqString in testFiles:
			print "Working on:", stdString+",",seqString
			with open(pJoin("inFiles",stdString),'r') as stdFile, open(pJoin("inFiles",seqString),'r') as seqFile:
				stdContents, seqContents = stdFile.read(), seqFile.read()
			# print "First few lines before encryption:\n", stdContents[:100]
			encData = encryptData(stdContents, key)
			with open(pJoin(workDir, "encryptedFiles", "Encrypted_"+stdString),"w+") as encFile:
				encFile.write(encData)
			encData = encryptData(seqContents, key)
			with open(pJoin(workDir, "encryptedFiles", "Encrypted_"+seqString),"w+") as encFile:
				encFile.write(encData)
			# print "First few lines after enc:\n", encData[:100]
			# Read and decrypt to convert to a .glm.
			with open(pJoin(workDir, "encryptedFiles", "Encrypted_"+stdString),'r') as inFile:
				encStdContents = inFile.read()
			with open(pJoin(workDir, "encryptedFiles", "Encrypted_"+seqString),'r') as inFile2:
				encSeqContents = inFile2.read()
			print "\nCreated encrypted files:", "Encrypted_"+stdString+",", "Encrypted_"+seqString
			# Decrypt.
			decStdContents = decryptData(encStdContents,key)
			decSeqContents = decryptData(encSeqContents,key)
			# print "First few lines after dec:\n", decStdContents[:100]
			# Convert to .glm.
			def runMilConvert(stdContents, seqContents):
				myFeed, xScale, yScale = omf.milToGridlab.convert(stdContents,seqContents)
				with open(pJoin(workDir,stdString.replace('.std','.glm')),'w') as outFile:
					outFile.write(omf.feeder.sortedWrite(myFeed))
				myGraph = omf.feeder.treeToNxGraph(myFeed)
				omf.feeder.latLonNxGraph(myGraph, neatoLayout=False)
				plt.savefig(pJoin(workDir,stdString.replace('.std','.png')))
				plt.close()
			if not os.path.isfile(pJoin(workDir,stdString.replace('.std','.glm'))):
				runMilConvert(decStdContents, decSeqContents)
				print "Converted std/seq to glm."
			# Convert converted .glm to encrypted glm.
			with open(pJoin(workDir,stdString.replace('.std','.glm')),'r') as inGLM:
				glmContents = inGLM.read()
			encData = encryptData(glmContents, key)
			with open(pJoin(workDir, "encryptedFiles","Encrypted_"+stdString.replace('.std','.glm')),'w') as encFile:
				encFile.write(encData)
			print "Encrypted glm file:", stdString.replace('.std','.glm')
			# Decrypt .glm, convert to .json.
			with open(pJoin(workDir, "encryptedFiles", "Encrypted_"+stdString.replace('.std','.glm')),'r') as encFile:
				encOutGlm = encFile.read()
			outGlm = decryptData(encOutGlm,key)
			newFeeder = gridlabImport(workDir, stdString.strip('.std'), outGlm)
			# Run gridlabD on decrypted GLM.
			if runGridlabD:
				output = gridlabd.runInFilesystem(newFeeder['tree'], attachments=testAttachments, keepFiles=False)
				if showGDLABResults:
					print "[STDERR]\n", (output['stderr'])
					print "[STDOUT]\n", (output['stdout'])
					print 'RAN GRIDLAB ON', stdString
			# Convert JSON to encrypted json.
			with open(pJoin(workDir,stdString.replace('.std','.json')),'r') as encFile:
				decJSON = encFile.read()
			encData = encryptData(decJSON, key)
			with open(pJoin(workDir,"encryptedFiles","Encrypted_"+stdString.replace('.std','.json')),'w') as encFile:
				encFile.write(encData)
			print "Encrypted JSON file:", stdString.replace('.std','.json')
			# Clean up unencrypted .glm and .json.
			if cleanUp:
				try:
					os.remove(pJoin(workDir,stdString.replace('.std','.glm')))
					print "Removed unencrypted file:", stdString.replace('.std','.glm')
				except: pass
				try:
					os.remove(pJoin(workDir,stdString.replace('.std','.json')))
					print "Removed unencrypted file:", stdString.replace('.std','.json')
				except: pass
		print "\nDone with encrypting all test files."
	except:
		print "Failed to encrypt", stdString, seqString
		exceptionCount += 1
		traceback.print_exc()
	return exceptionCount

if __name__ == "__main__":
	_tests()