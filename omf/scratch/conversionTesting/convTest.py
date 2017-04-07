# Note: While trying to debug, I re-encrypted most of the files. The files in the doNotConvert... folder 
# are now encrypted a different way than the ones in the encryptedFiles folder. Because of this they will not decrypt
import os, json, traceback, shutil, sys
from os.path import join as pJoin
import matplotlib
from matplotlib import pyplot as plt
from cryptography.fernet import Fernet
# OMF Functions
import omf
import cymeToGridlab
import milToGridlab
from solvers import gridlabd

# Paths
_myDir = os.path.dirname(os.path.abspath(__file__))
_cryptoPath = _myDir
sys.path.insert(0,_cryptoPath)

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

def convertFiles(user, inFolder, outFolder):
	''' Encrypt files in inFolder to outFolder. '''
	key = getKey(_cryptoPath,user)
	for file in os.listdir(inFolder):
		fileName = "Encrypted_"+str(file)
		with open(pJoin(inFolder,str(file)),'r') as r:
					r = r.read()
		encryptedData = encryptData(r,key)
		with open(pJoin(outFolder,fileName),"w+") as f:
			f.write(encryptedData)

def addEncryptedFiles(inFilesFolder="needEncryption"):
	''' Encrypt files in inFilesFolder as addition to test set.'''
	user = "convTest"
	newFilesFolderPath = pJoin(_cryptoPath,"encryptedFiles")
	inFolderPath = pJoin(_cryptoPath,inFilesFolder)
	convertFiles(user, inFolderPath, newFilesFolderPath)

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
	seqFilenames = []
	stdFilenames = []
	mdbFilenames = []
	milTestArray = []
	for file in os.listdir(decryptedDataFolder):
		if str(file).endswith('.mdb'):
			mdbFilenames.append(file)
		if str(file).endswith('.seq'):
			filename = file[:-4]
			seqFilenames.append(file)
		if str(file).endswith('.std'):
			filename = file[:-4]
			stdFilenames.append(file)
	seqFilenames.sort()
	stdFilenames.sort()
	milTestArray = zip(stdFilenames, seqFilenames)
	# Runs milsoft tests on seq std files and then deletes results and decrypted files
	openPrefix = './decryptedDataFiles/'
	outPrefix = './milToGridlabTests/'
	cymeOutPre = './cymeToGridlabTests/'
	testAttachments = {'schedules.glm':'', 'climate.tmy2':open('./decryptedDataFiles/AK-ANCHORAGE.tmy2','r').read()}
	milToGridlab._tests(milTestArray, openPrefix, outPrefix, testAttachments)
	# Runs cyme tests on .mdb files
	cymeToGridlab._tests(mdbFilenames, openPrefix, cymeOutPre)
	# Combine the two results files
	filenames = [pJoin(outPrefix,'convResults.txt'), pJoin(cymeOutPre,'convResults.txt')]
	# Creating results file
	with open('conversionResults.txt', 'w') as outfile:
		for fname in filenames:
			with open(fname) as infile:
				for line in infile:
					outfile.write(line)
	# Delete Test folders
	if(os.path.isdir('./milToGridlabTests/')):
		shutil.rmtree('./milToGridlabTests/')
	if(os.path.isdir('./cymeToGridlabTests/')):
		shutil.rmtree('./cymeToGridlabTests/')	
	# Delete decrypted files after tests
	if(os.path.isdir(decryptedDataFolder)):
		shutil.rmtree(decryptedDataFolder)
	print "finished"

if __name__ == "__main__":
	_tests()
	# addEncryptedFiles()
