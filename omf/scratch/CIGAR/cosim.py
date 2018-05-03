import os, urllib, urllib2, subprocess, time

PORT = '6267'
BASE_URL = 'http://localhost:' + PORT + '/'
GLM_PATH = './smsSingle.glm'
START_PAUSE = '2000-01-02 00:00:00'

def waitUntil(targetTime):
	# Step to targetTime in current simulation.
	# TODO: do real URL encoding?
	niceUrl = BASE_URL + 'control/pauseat=' + targetTime.replace(' ','%20')
	urllib2.urlopen(niceUrl).read()
	currentTime = None
	while currentTime != targetTime:
		time.sleep(1)
		#HACK: Read clock and also drop the timezone because it causes problems.
		currentTime = urllib2.urlopen(BASE_URL + 'raw/clock').read()[0:-4]
		# print 'CURRENT VS TARGET', currentTime, targetTime
		#TODO: need a maxWait argument and accumulator so we don't wait forever.

#TODO: def read(obName, propName). If urlopen fails, do warnings.warn() instead of raise exception.
#TODO: def write(obName, propName, value) = read(obName, propName += '=value')

# Start servert in server mode, note that the .glm has pauseat set for 1 day in to the simulation.
proc = subprocess.Popen(['gridlabd', GLM_PATH, '--server', '-P', PORT, '-q','--define','pauseat="' + START_PAUSE + '"'], stderr=None, stdout=None)
# Hack: wait for the dang server to start up and simulate.
time.sleep(2)
#TODO: instead of sleeping, wait 1 second, try to read clock, if it fails then wait 1 more second, loop, etc.

# Read the clock, solar output voltage, battery state of charge, and inverter voltage input.
print '* Reading clock:', urllib2.urlopen(BASE_URL + 'raw/clock').read()
print '* Reading solar_1 output volatage (V_Out):', urllib2.urlopen(BASE_URL + 'raw/solar_1/V_Out').read()
# print '* Reading battery_1 state of charge:', urllib2.urlopen(BASE_URL + 'raw/battery_1/battery_state').read()
print '* Reading inverter_1 input voltage (V_In):', urllib2.urlopen(BASE_URL + 'raw/inverter_1/V_In').read()
# Step the simulation.
waitUntil('2000-01-02 12:00:00')
print '* Stepped ahead 12 hours.'
# Get the value and clock again.
print '* Reading solar_1 output voltage (V_Out):', urllib2.urlopen(BASE_URL + 'raw/solar_1/V_Out').read()
#	print '* Reading battery_1 state of charge:', urllib2.urlopen(BASE_URL + 'raw/battery_1/battery_state').read()
print '* Reading inverter_1 input voltage (V_In):', urllib2.urlopen(BASE_URL + 'raw/inverter_1/V_In').read()
print '* Reading clock again:', urllib2.urlopen(BASE_URL + 'raw/clock').read()
# # Set a value.
# urllib2.urlopen(BASE_URL + 'raw/waterheater1/temperature=110.0').read()
# print '* Setting temp to 110.'
# Finish the simulation and see final values.
print '* Resuming simulation.'
urllib2.urlopen(BASE_URL + 'control/resume').read()
print '* Reading solar_1 output volatage (V_Out):', urllib2.urlopen(BASE_URL + 'raw/solar_1/V_Out').read()
#	print '* Reading battery_1 state of charge:', urllib2.urlopen(BASE_URL + 'raw/battery_1/battery_state').read()
print '* Reading inverter_1 input voltage (V_In):', urllib2.urlopen(BASE_URL + 'raw/inverter_1/V_In').read()

# Stop the simulation.
try:
	print '* Sending shutdown.'
	urllib2.urlopen(BASE_URL + 'control/shutdown')
except:
	pass # should be shut down now.
# proc.kill() # For those hard-to-stop servers.
