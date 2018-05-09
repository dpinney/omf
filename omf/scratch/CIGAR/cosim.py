import os, urllib, urllib2, subprocess, time, warnings

# Inputs.
PORT = '6267'
HOST = 'localhost'
GLM_PATH = './smsSingle.glm'
START_PAUSE = '2000-01-02 00:00:00'

# Globals.
baseUrl = 'http://' + HOST + ':' + PORT + '/'

def _request(reqType, arg1, arg2=None, arg3=None):
	pass #TODO: refactor to use this for each other command.

def waitUntil(targetTime):
	'Step to targetTime in current simulation.'
	try:
		# HACK: we don't need full URL encoding right?
		niceUrl = baseUrl + 'control/pauseat=' + targetTime.replace(' ','%20')
		urllib2.urlopen(niceUrl).read()
		currentTime = None
		while currentTime != targetTime:
			time.sleep(1)
			#HACK: Read clock and also drop the timezone because it causes problems.
			currentTime = urllib2.urlopen(baseUrl + 'raw/clock').read()[0:-4]
	except:
		warnings.warn("Wait until failed!")

def read(obName, propName):
	'Read a value from the GLD simulation.'
	try:
		return urllib2.urlopen(baseUrl + 'raw/' + obName + '/' + propName).read()
	except:
		warnings.warn("Failed to read " + propName + " of " + obName)

def readClock():
	'Read the clock'
	try:
		return urllib2.urlopen(baseUrl + 'raw/clock').read()
	except:
		warnings.warn("Failed to read the clock.")

def shutdown():
	'Stop simulation.'
	try:
		return urllib2.urlopen(baseUrl + 'control/shutdown').read()
	except:
		warnings.warn("Shutdown failed!")

def resume():
	try:
		return urllib2.urlopen(baseUrl + 'control/resume').read()
	except:
		warnings.warn("Resume failed!")

def write(obName, propName, value):
	'Write a value back to the simulation'
	#HACK: writing is just reading a value plus a little bit more.
	read(obName, propName + '=' + value)

def start():
	#TODO: watch out for in-use port.
	proc = subprocess.Popen(['gridlabd', GLM_PATH, '--server', '-P', PORT, '-q','--define','pauseat="' + START_PAUSE + '"'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
	# HACK: wait for the dang server to start up and simulate.
	time.sleep(2) #TODO: instead of sleeping, wait 1 second, try to read clock, if it fails then wait 1 more second, loop, etc.

def _test():
	start()
	# Read the clock, solar output voltage, battery state of charge, and inverter voltage input.
	print '* Reading clock:', readClock()
	print '* Reading solar_1 output volatage (V_Out):', read('solar_1', 'V_Out')
	# print '* Reading battery_1 state of charge:', urllib2.urlopen(baseUrl + 'raw/battery_1/battery_state').read()
	print '* Reading inverter_1 input voltage (V_In):', read('inverter_1','V_In')
	# Step the simulation.
	waitUntil('2000-01-02 12:00:00')
	print '* Stepped ahead 12 hours.'
	# Get the value and clock again.
	print '* Reading solar_1 output voltage (V_Out):', read('solar_1','V_Out')
	#	print '* Reading battery_1 state of charge:', urllib2.urlopen(baseUrl + 'raw/battery_1/battery_state').read()
	print '* Reading inverter_1 input voltage (V_In):', read('inverter_1','V_In')
	print '* Reading clock again:', readClock()
	# # Set a value.
	write('waterheater1','temperature','110.0')
	print '* Setting temp to 110.'
	# Finish the simulation and see final values.
	print '* Resuming simulation.'
	resume()
	print '* Reading solar_1 output volatage (V_Out):', read('solar_1','V_Out')
	print '* Reading final temp:', read('waterheater1','temperature')
	#	print '* Reading battery_1 state of charge:', urllib2.urlopen(baseUrl + 'raw/battery_1/battery_state').read()
	print '* Reading inverter_1 input voltage (V_In):', read('inverter_1','V_In')
	# Stop the simulation.
	# shutdown()
	# proc.kill() # For those hard-to-stop servers.

if __name__ == '__main__':
	_test()