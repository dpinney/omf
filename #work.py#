'''
Work executes python functions. It can use the local machine or the omf.coop cluster.

One queue, stores tuples (analysisName, requestType). Or maybe have two queues, whatever.

Adding jobs.
	Put (analysisName, 'toRun') on the queue.
	If that analysis is already on the queue, return failed.
	Update the DB to say queued.
Running jobs.
	Every 1(?) second, all nodes check the queue.
	If there's a toRun there, and we're not full, pop one.
	Start the job.
	Update DB to say queued.
Canceling jobs.
	Every 1(?) second, all nodes check the queue.
	If there's a toKill there, and we're running that analysisName, pop one.
	Kill the PID.

Queue limits?

We need to handle two cases:
1. Filesystem case. Just have a dumb fileQueue class that has no limits, etc.?
2. S3 cluster case. Have a cluterQueue class, and also have a daemon.
'''

import os, tempfile, time
from multiprocessing import Value, Lock
from threading import Thread, Timer
import studies, analysis, milToGridlab

JOB_LIMIT = 1

class MultiCounter(object):
	def __init__(self, initval=0):
		self.val = Value('i', initval)
		self.lock = Lock()
	def increment(self):
		with self.lock:
			self.val.value += 1
	def decrement(self):
		with self.lock:
			self.val.value -= 1
	def value(self):
		with self.lock:
			return self.val.value

class LocalWorker:
	def __init__(self):
		self.runningJobCount = MultiCounter(0)
		self.jobRecorder = {}
	def run(self, analysisObject, store):
		runThread = Thread(name=analysisObject.name, target=self.runInBackground, args=[analysisObject, store])
		self.jobRecorder[time.time()] = runThread
		runThread.start()

	def _studyInstance(self, studyName, anaObject, store):
		studyData = store.get('Study', anaObject.name + '---' + studyName)
		studyData.update({'name':studyName,'analysisName':anaObject.name})
		moduleRef = getattr(studies, studyData['studyType'])
		classRef = getattr(moduleRef, studyData['studyType'].capitalize())
		return classRef(studyData)

	def runInBackground(self, anaObject, store):
		# Setup.
		self.runningJobCount.increment()

		studyList = [self._studyInstance(studyName, anaObject, store) for studyName in anaObject.studyNames]
		# Run.
		anaObject.run(studyList)
		# Storing result.
		store.put('Analysis', anaObject.name, anaObject.__dict__)
		for study in studyList:
			store.put('Study', study.analysisName + '---' + study.name, study.__dict__)
		self.runningJobCount.decrement()
	def milImport(self, store, feederName, stdString, seqString):
		# Setup.
		self.runningJobCount.increment()
		importThread = Thread(target=self.milImportBackground, args=[store, feederName, stdString, seqString])
		importThread.start()
		self.runningJobCount.decrement()

	def boilerplate(func):
		newFeeder = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5','linkDistance':'5','charge':'-5'}}
		func(newFeeder)
		with open('./schedules.glm','r') as schedFile:
			newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
		store.put('Feeder', feederName, newFeeder)
		# store.delete('Conversion', feederName)


	def milImportBackground(self, store, feederName, stdString, seqString):
		newFeeder = {'links':[],'hiddenLinks':[],'nodes':[],'hiddenNodes':[],'layoutVars':{'theta':'0.8','gravity':'0.01','friction':'0.9','linkStrength':'5','linkDistance':'5','charge':'-5'}}
		[newFeeder['tree'], xScale, yScale] = milToGridlab.convert(stdString, seqString)
		newFeeder['layoutVars']['xScale'] = xScale
		newFeeder['layoutVars']['yScale'] = yScale
		with open('./schedules.glm','r') as schedFile:
			newFeeder['attachments'] = {'schedules.glm':schedFile.read()}
		store.put('Feeder', feederName, newFeeder)
		store.delete('Conversion', feederName)

	def _killingInTheName(self, anaName):
		try: 
			for runDir in os.listdir('running'):
				if runDir.startswith(anaName + '---'):
					with open('running/' + runDir + '/PID.txt','r') as pidFile:
						os.kill(int(pidFile.read()), 15)
						print 'Terminated', anaName
						return True
		except:
			print 'Missed attempt to terminate', anaName
			return False

	def terminate(self, anaName):
		# Try to kill three times.
		for attempt in range(3):
			if self._killingInTheName(anaName): break
			time.sleep(2)
	def status(self):
		return [[key,self.jobRecorder[key].name,self.jobRecorder[key].is_alive()] for key in self.jobRecorder]