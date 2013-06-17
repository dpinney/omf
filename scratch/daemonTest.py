#!/usr/bin/env python

def scheduleSomeJobs():
	import sched, time
	def job():
		print 'Working now at time', time.time()
	mySched = sched.scheduler(time.time, time.sleep)
	job1 = mySched.enter(1, 1, job, [])
	job2 = mySched.enter(2, 1, job, [])
	job3 = mySched.enter(3, 1, job, [])
	# Actually only run 2 jobs:
	mySched.cancel(job2)
	mySched.run()

def endlessLoop():
	from threading import Timer
	def repeating():
		print 'Hello!'
		# Repeat every 2ish seconds:
		Timer(2.302, repeating).start()
	# Begin execution:
	repeating()

def writeToSQS():
	from boto.sqs.connection import SQSConnection
	import time
	conn = SQSConnection('AKIAIFNNIT7VXOXVFPIQ', 'stNtF2dlPiuSigHNcs95JKw06aEkOAyoktnWqXq+')
	q = conn.get_queue('crnOmfJobQueue')
	m = q.new_message('Test Message ' + str(time.time()))
	q.write(m)

def pingSQS():
	from boto.sqs.connection import SQSConnection
	conn = SQSConnection('AKIAIFNNIT7VXOXVFPIQ', 'stNtF2dlPiuSigHNcs95JKw06aEkOAyoktnWqXq+')
	q = conn.get_queue('crnOmfJobQueue')
	print 'OMF message count:', q.count()

def endlessPinging():
	from threading import Timer
	def repeating():
		pingSQS()
		Timer(2, repeating).start()
	repeating()

if __name__ == '__main__':
	endlessPinging()

'''
One queue, stores tuples (analysisName, requestType). Or maybe have two queues, whatever.

Adding jobs.
	Put (analysisName, 'toRun') on the queue.
	If that analysis is already on the queue, return failed.
	Update the DB to say queued.
Running jobs.
	Every 1(?) second, all nodes check the queue.
	If there's a toRun there, and we're not full, pop it.
	Start the job.
	Update DB to say queued.
Canceling jobs.
	Every 1(?) second, all nodes check the queue.
	If there's a toKill there, and we're running that analysisName, pop it.
	Kill the PID.

Queue limits?


We need to handle two cases:
1. Filesystem case. Just have a dumb fileQueue class that has no limits, etc.?
2. S3 cluster case. Have a cluterQueue class, and also have a daemon.

'''

class LocalQueue:
	def __init__(self, localOrRemote):
		pass
	
	def addJob(self, jobOb):
		pass

	def killJob(self, jobOb):
		pass

class ClusterQueue:
	pass