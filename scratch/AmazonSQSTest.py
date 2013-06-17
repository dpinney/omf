#!/usr/bin/env python

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
conn = SQSConnection('AKIAIFNNIT7VXOXVFPIQ', 'stNtF2dlPiuSigHNcs95JKw06aEkOAyoktnWqXq+')
q = conn.get_queue('dwpTestQueue')

def writeToSQS(messageBody):
	# Note that messages are base64 encoded.
	m1 = Message()
	m1.set_body(messageBody)
	q.write(m1)

def pingSQS():
	print 'OMF message count:', q.count()

def peakSingleMessage():
	print [m.get_body() for m in q.get_messages(1)]

def eatSingleMessage():
	pull = q.get_messages(1)
	if len(pull) == 0:
		return False
	else:
		m = pull[0]
		q.delete_message(m)
		return m.get_body()

def endlessPinging():
	from threading import Timer
	def repeating():
		pingSQS()
		Timer(2, repeating).start()
	repeating()

if __name__ == '__main__':
	# writeToSQS('Test message!')
	# endlessPinging()
	print eatSingleMessage()


