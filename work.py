
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

import multiprocessing
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

class LocalQueue:
	def __init__(self):
		pass
	def executeAnalysis(self, jobOb):
		pass
	def terminateAnalysis(self, jobOb):
		pass

class ClusterQueue:
	def __init__(self, userKey, passKey, workQueueName, terminateQueueName):
		self.runningJobs = 0
		self.conn = SQSConnection(userKey, passKey)
		self.workQueue = self.conn.get_queue(workQueueName)
		self.terminateQueue = self.conn.get_queue(terminateQueueName)
	def queueWork(self, analysisName):
		m = Message()
		m.set_body(analysisName)
		status = self.workQueue.write(m)
		return status
	def queueTerminate(self, analysisName):
		m = Message()
		m.set_body(analysisName)
		status = self.terminateQueue(m)
		return status

def monitorClusterQueue():
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