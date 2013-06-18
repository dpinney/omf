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
import os, multiprocessing
import studies
from threading import Timer
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message

JOB_LIMIT=1

class backgroundProc(multiprocessing.Process):
	def __init__(self, backFun, funArgs):
		self.name = 'omfWorkerProc'
		self.backFun = backFun
		self.funArgs = funArgs
		self.myPid = os.getpid()
		multiprocessing.Process.__init__(self)
	def run(self):
		self.backFun(*self.funArgs)

class LocalWorker:
	def __init__(self):
		pass
	def run(self, analysisObject, store):
		runProc = backgroundProc(self.runInBackground, [analysisObject, store])
		runProc.start()
	def runInBackground(self, anaObject, store):
		def studyInstance(studyName):
			studyData = store.get('Study', anaObject.name + '---' + studyName)
			studyData.update({'name':studyName,'analysisName':anaObject.name})
			moduleRef = getattr(studies, studyData['studyType'])
			classRef = getattr(moduleRef, studyData['studyType'].capitalize())
			return classRef(studyData)
		studyList = [studyInstance(studyName) for studyName in anaObject.studyNames]
		anaObject.run(studyList)
		store.put('Analysis', anaObject.name, anaObject.__dict__)
		for study in studyList:
			store.put('Study', study.analysisName + '---' + study.name, study.__dict__)
	def terminate(self, anaName):
		for runDir in os.listdir('running'):
			if runDir.startswith(anaName + '---'):
				try:
					with open('running/' + runDir + '/PID.txt','r') as pidFile:
						os.kill(int(pidFile.read()), 15)
				except:
					pass

class ClusterWorker:
	def __init__(self, userKey, passKey, workQueueName, terminateQueueName):
		self.conn = SQSConnection(userKey, passKey)
		self.workQueue = self.conn.get_queue(workQueueName)
		self.terminateQueue = self.conn.get_queue(terminateQueueName)
	def run(self, analysisObject, store):
		m = Message()
		m.set_body(analysisName)
		status = self.workQueue.write(m)
		return status
	def terminate(self, analysisObject, store):
		m = Message()
		m.set_body(analysisName)
		status = self.terminateQueue(m)
		return status

def monitorClusterQueue():
	print 'Entering Daemon Mode.'
	import omf
	conn = SQSConnection('AKIAISPAZIA6NBEX5J3A', omf.USER_PASS)
	jobQueue = conn.get_queue('crnOmfJobQueue')
	terminateQueue = conn.get_queue('crnOmfTerminateQueue')
	runningJobs = 0
	def popJob(queueName):
		mList = queueName.get_messages(1)
		if len(mList) == 1:
			anaName = mList[0].get_body()
			queueName.delete_message(mList[0])
			return anaName
		else:
			return False
	def endlessLoop():
		if runningJobs < JOB_LIMIT:
			anaName = popJob(jobQueue)
			if anaName != False:
				runningJobs += 1
				# TODO: Get analysis stuff from storage, run it here.
				pass
		if runningJobs > 0:
			anaName = popJob(terminateQueue)
			if anaName != False:
				# TODO: Try to terminate. 
				if TERMINATION_SUCCESS: runningJobs -= 1
		# Check again in 1 second:
		Timer(1, repeating).start()
	endlessLoop()

if __name__ == '__main__':
	# If we're running this module directly, go into daemon mode:
	monitorClusterQueue()