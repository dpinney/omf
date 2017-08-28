import os, urllib2, subprocess, time

# Start servert in server mode, note that the .glm has pauseat set for 1 day in to the simulation.
proc = subprocess.Popen(['gridlabd','smsSingle.glm','--server','-P','6267'],stderr=None, stdout=None)
# Hack: wait for the dang server to start up and simulate.
time.sleep(2)

try:
	# Read the clock and a water heater temp.
	print urllib2.urlopen('http://localhost:6267/clock').read()
	print urllib2.urlopen('http://localhost:6267/waterheater1/temperature').read()
	# Step the simulation.
	urllib2.urlopen('http://localhost:6267/control/pauseat=2000-01-02%2012:00:00').read()
	print 'Stepped ahead 12 hours.'
	time.sleep(2) # Hack: give the simulation some time to run.
	# Get the value and clock again.
	print urllib2.urlopen('http://localhost:6267/waterheater1/temperature').read()
	print urllib2.urlopen('http://localhost:6267/clock').read()
	# Set a value.
	urllib2.urlopen('http://localhost:6267/waterheater1/temperature=110.0').read()
	# Finish the simulation and see final temperature.
	urllib2.urlopen('http://localhost:6267/control/resume').read()
	print urllib2.urlopen('http://localhost:6267/waterheater1/temperature').read()
except:
	pass # server being weird.

# Stop the simulation.
try:
	urllib2.urlopen('http://localhost:6267/control/shutdown')
except:
	pass # should be shut down now.
print proc.stdout
# proc.kill() # For those hard-to-stop servers.
