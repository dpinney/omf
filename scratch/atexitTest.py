''' Can we clean up model runs using the atexit module? Or we could just do two layers of child process... '''

import multiprocessing

def sleepFun():
	import time, atexit
	@atexit.register
	def goodbye():
		print "CLEANING UP CHILD PROCESS HERE."
	time.sleep(4)
	print "NATURAL COMPLETION."

backProc = multiprocessing.Process(target=sleepFun)
# backProc.start() DO NOT START THIS IT WILL FORKBOMB
print "Started background process."

''' Results:
Ctrl-C killing does trigger goodbye().
Task manager does NOT trigger goodbye().
Trying to launch a sleepFun results in FORKBOMB!!!
'''