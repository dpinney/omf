#!/usr/bin/env python

import sys, struct

if sys.platform == 'win32' or sys.platform == 'cygwin':
	if 8*struct.calcsize("P") == 64:
		_dll = CDLL("solvers/nrelsam/ssc64.dll") 
	else:
		_dll = CDLL("solvers/nrelsam/ssc32.dll") 
elif sys.platform == 'darwin':
	_dll = CDLL("solvers/nrelsam/ssc64.dylib") 
elif sys.platform == 'linux2':
	_dll = CDLL("solvers/nrelsam/ssc64.so") 
else:
	print "Platform not supported ", sys.platform