#!/usr/bin/env python

'''
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

import os, tempfile, psutil
from multiprocessing import Process, Value, Lock
import studies, analysis
from threading import Timer
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message

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
		self.jobRecorder = []
	def run(self, analysisObject, store):
		runProc = Process(name=analysisObject.name, target=self.runInBackground, args=[analysisObject, store])
		self.jobRecorder.append(runProc)
		runProc.start()
	def runInBackground(self, anaObject, store):
		# Setup.
		self.runningJobCount.increment()
		def studyInstance(studyName):
			studyData = store.get('Study', anaObject.name + '---' + studyName)
			studyData.update({'name':studyName,'analysisName':anaObject.name})
			moduleRef = getattr(studies, studyData['studyType'])
			classRef = getattr(moduleRef, studyData['studyType'].capitalize())
			return classRef(studyData)
		studyList = [studyInstance(studyName) for studyName in anaObject.studyNames]
		# Run.
		anaObject.run(studyList)
		# Storing result.
		store.put('Analysis', anaObject.name, anaObject.__dict__)
		for study in studyList:
			store.put('Study', study.analysisName + '---' + study.name, study.__dict__)
		self.runningJobCount.decrement()
	def terminate(self, anaName):
		for runDir in os.listdir('running'):
			if runDir.startswith(anaName + '---'):
				try:
					with open('running/' + runDir + '/PID.txt','r') as pidFile:
						os.kill(int(pidFile.read()), 15)
				except:
					pass
	def status(self):
		return [[row.name,row.pid,row.is_alive()] for row in self.jobRecorder]


class ClusterWorker:
	def __init__(self, userKey, passKey, workQueueName, terminateQueueName, store):
		self.conn = SQSConnection(userKey, passKey)
		self.workQueue = self.conn.get_queue(workQueueName)
		self.terminateQueue = self.conn.get_queue(terminateQueueName)
		# Start polling for jobs on launch:
		tempPath = os.path.join(tempfile.gettempdir(),'omfWorker.pid')
		def touchOpen(filename, *args, **kwargs):
			# Open the file in R/W and create if it doesn't exist. *Don't* pass O_TRUNC
			fd = os.open(filename, os.O_RDWR | os.O_CREAT)
			# Encapsulate the low-level file descriptor in a python file object
			return os.fdopen(fd, *args, **kwargs)
		try:
			if not os.path.isfile(tempPath):
				with touchOpen(tempPath, 'w') as newLock:
					pollerProc = Process(name='pollerProc',target=self.__monitorClusterQueue__, args=[passKey, store])
					pollerProc.start()
					newLock.write(str(pollerProc.pid))
			else:
				with open(tempPath, 'r+b') as pidFile:
					fileContents = pidFile.read()
					try:
						pid = int(fileContents)
					except:
						pid = -999
					if not psutil.pid_exists(pid):
						pollerProc = Process(name='pollerProc',target=self.__monitorClusterQueue__, args=[passKey, store])
						pollerProc.start()
						pidFile.seek(0)
						pidFile.write(str(pollerProc.pid))
		except:
			# Debug code. Will spit garbage on the regular:
			import traceback
			traceback.print_exc()
			# Something else probably had the write lock, so give up in this thread:
			pass
	def run(self, analysisObject, store):
		m = Message()
		m.set_body(analysisObject.name)
		status = self.workQueue.write(m)
		return status
	def terminate(self, anaName):
		m = Message()
		m.set_body(anaName)
		status = self.terminateQueue.write(m)
		return status
	def __monitorClusterQueue__(self, passKey, store):
		print 'Entering Daemon Mode.'
		conn = SQSConnection('AKIAISPAZIA6NBEX5J3A', passKey)
		jobQueue = conn.get_queue('crnOmfJobQueue')
		terminateQueue = conn.get_queue('crnOmfTerminateQueue')
		daemonWorker = LocalWorker()
		def popJob(queueObject):
			mList = queueObject.get_messages(1)
			if len(mList) == 1:
				anaName = mList[0].get_body()
				queueObject.delete_message(mList[0])
				return anaName
			else:
				return False
		def endlessLoop():
			print os.getpid()
			print daemonWorker.status()
			if daemonWorker.runningJobCount.value() < JOB_LIMIT:
				anaName = popJob(jobQueue)
				if anaName != False:
					print 'Daemon running', anaName
					thisAnalysis = analysis.Analysis(store.get('Analysis', anaName))
					daemonWorker.run(thisAnalysis, store)
			if daemonWorker.runningJobCount.value() > 0:
				anaName = popJob(terminateQueue)
				if anaName != False:
					print 'Daemon terminating', anaName
					daemonWorker.terminate(anaName)
			# Check again in 1 second:
			Timer(1, endlessLoop).start()
		endlessLoop()
	def status(self):
		return []
