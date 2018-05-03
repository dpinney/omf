import os, urllib2, subprocess, time

# Start servert in server mode, note that the .glm has pauseat set for 1 day in to the simulation.
proc = subprocess.Popen(['gridlabd','smsSingle.glm','--server','-P','6267','-q'],stderr=None, stdout=None)
# Hack: wait for the dang server to start up and simulate.
time.sleep(2)

BASE_URL = 'http://localhost:6267/'

def waitUntil(datetime):
	# Step to datetime
	urllib2.urlopen(BASE_URL + 'control/pauseat=' + datetime).read()
	currentTime = None
	while currentTime != datetime:
		time.sleep(1)
		# Read clock:
		currentTime = urllib2.urlopen(BASE_URL + 'raw/clock').read()

try:
	# # Read the clock and a water heater temp.
	# print '* Reading clock:', urllib2.urlopen(BASE_URL + 'raw/clock').read()
	# print '* Reading heater temp:', urllib2.urlopen(BASE_URL + 'raw/waterheater1/temperature').read()
	# # Step the simulation.
	# urllib2.urlopen(BASE_URL + 'control/pauseat=2000-01-02%2012:00:00').read()
	# print '* Stepped ahead 12 hours.'
	# time.sleep(2) # Hack: give the simulation some time to run.
	# # Get the value and clock again.
	# print '* Reading temp again:', urllib2.urlopen(BASE_URL + 'raw/waterheater1/temperature').read()
	# print '* Reading clock again:', urllib2.urlopen(BASE_URL + 'raw/clock').read()
	# # Set a value.
	# urllib2.urlopen(BASE_URL + 'raw/waterheater1/temperature=110.0').read()
	# print '* Setting temp to 110.'
	# # Finish the simulation and see final temperature.
	# print '* Resuming simulation.'
	# urllib2.urlopen(BASE_URL + 'control/resume').read()
	# print '* Reading final temp:', urllib2.urlopen(BASE_URL + 'raw/waterheater1/temperature').read()

	# Read the clock, solar output voltage, battery state of charge, and inverter voltage input.
	print '* Reading clock:', urllib2.urlopen(BASE_URL + 'raw/clock').read()
	print '* Reading solar_1 output volatage (V_Out):', urllib2.urlopen(BASE_URL + 'raw/solar_1/V_Out').read()
#	print '* Reading battery_1 state of charge:', urllib2.urlopen(BASE_URL + 'raw/battery_1/battery_state').read()
	print '* Reading inverter_1 input voltage (V_In):', urllib2.urlopen(BASE_URL + 'raw/inverter_1/V_In').read()
	# Step the simulation.
	urllib2.urlopen(BASE_URL + 'control/pauseat=2000-01-02%2012:00:00').read()
	print '* Stepped ahead 12 hours.'
	time.sleep(2) # Hack: give the simulation some time to run.
	# Get the value and clock again.
	print '* Reading solar_1 output volatage (V_Out):', urllib2.urlopen(BASE_URL + 'raw/solar_1/V_Out').read()
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
except:
	pass # server being weird.

# Stop the simulation.
try:
	print '* Sending shutdown.'
	urllib2.urlopen('http://localhost:6267/control/shutdown')
except:
	pass # should be shut down now.
# proc.kill() # For those hard-to-stop servers.
