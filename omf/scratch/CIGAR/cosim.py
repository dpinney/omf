import os, urllib, urllib2, subprocess, time, warnings


class Coordinator(object):
	agents = []
	MIN_STEP = 15 # in minutes
	
	def __init__(self, agents, cosimProps):
		self.agents = agents
		# Start the simulation
		cosim.start(cosimProps)
		stepNum = cosimProps.simLength / MIN_STEP
		# Step through each time step.
		for s in range(stepNum):
			# At each time step each agent acts.
			for a in agents:
				# Send agent's request to GridLAB-D
				rez = cosim.reqList(a.req(s))
				# Send results from GridLAB-D back to agent.
				a.feedback(rez)
			cosim.waitUntil(s + 1)

	def drawResults(self):
		pass #TODO: need an HTML table.


class GridLabWorld(object):
	def __init__(self, PORT, HOST, GLM_PATH, START_PAUSE):
		self.PORT = PORT
		self.HOST = HOST
		self.GLM_PATH = GLM_PATH
		self.START_PAUSE = START_PAUSE
		# Derived global.
		self.baseUrl = 'http://' + HOST + ':' + PORT + '/'

	def _request(self, reqType, arg1, arg2=None, arg3=None):
		pass #TODO: refactor to use this for each other command.

	def reqList(self):
		pass #TODO: take a list of requests {}, do them.

	def waitUntil(self, targetTime):
		'Step to targetTime in current simulation.'
		try:
			# HACK: we don't need full URL encoding right?
			niceUrl = self.baseUrl + 'control/pauseat=' + targetTime.replace(' ','%20')
			urllib2.urlopen(niceUrl).read()
			currentTime = None
			while currentTime != targetTime:
				time.sleep(1)
				#HACK: Read clock and also drop the timezone because it causes problems.
				currentTime = urllib2.urlopen(self.baseUrl + 'raw/clock').read()[0:-4]
		except:
			warnings.warn("Wait until failed!")

	def read(self, obName, propName):
		'Read a value from the GLD simulation.'
		try:
			return urllib2.urlopen(self.baseUrl + 'raw/' + obName + '/' + propName).read()
		except:
			warnings.warn("Failed to read " + propName + " of " + obName)

	def readClock(self):
		'Read the clock'
		try:
			return urllib2.urlopen(self.baseUrl + 'raw/clock').read()
		except:
			warnings.warn("Failed to read the clock.")

	def shutdown(self):
		'Stop simulation.'
		try:
			return urllib2.urlopen(self.baseUrl + 'control/shutdown').read()
		except:
			warnings.warn("Shutdown failed!")

	def resume(self):
		try:
			return urllib2.urlopen(self.baseUrl + 'control/resume').read()
		except:
			warnings.warn("Resume failed!")

	def write(self, obName, propName, value):
		'Write a value back to the simulation'
		#HACK: writing is just reading a value plus a little bit more.
		self.read(obName, propName + '=' + value)

	def start(self):
		#TODO: watch out for in-use port.
		proc = subprocess.Popen(['gridlabd', self.GLM_PATH, '--server', '-P', self.PORT, '-q','--define','pauseat="' + self.START_PAUSE + '"'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
		# HACK: wait for the dang server to start up and simulate.
		time.sleep(2) #TODO: instead of sleeping, wait 1 second, try to read clock, if it fails then wait 1 more second, loop, etc.

def _test():
	glw = GridLabWorld('6267', 'localhost', './smsSingle.glm', '2000-01-02 00:00:00')
	glw.start()
	# Read the clock, solar output voltage, battery state of charge, and inverter voltage input.
	print '* Reading clock:', glw.readClock()
	print '* Reading solar_1 output volatage (V_Out):', glw.read('solar_1', 'V_Out')
	# print '* Reading battery_1 state of charge:', glw.read('battery_1' + 'battery_state')
	print '* Reading inverter_1 input voltage (V_In):', glw.read('inverter_1','V_In')
	# Step the simulation.
	glw.waitUntil('2000-01-02 12:00:00')
	print '* Stepped ahead 12 hours.'
	# Get the value and clock again.
	print '* Reading solar_1 output voltage (V_Out):', glw.read('solar_1','V_Out')
	#	print '* Reading battery_1 state of charge:', glw.read('battery_1' + 'battery_state')
	print '* Reading inverter_1 input voltage (V_In):', glw.read('inverter_1','V_In')
	print '* Reading clock again:', glw.readClock()
	# # Set a value.
	glw.write('waterheater1','temperature','110.0')
	print '* Setting temp to 110.'
	# Finish the simulation and see final values.
	print '* Resuming simulation.'
	glw.resume()
	print '* Reading solar_1 output volatage (V_Out):', glw.read('solar_1','V_Out')
	print '* Reading final temp:', glw.read('waterheater1','temperature')
	#	print '* Reading battery_1 state of charge:', glw.read('battery_1' + 'battery_state')
	print '* Reading inverter_1 input voltage (V_In):', glw.read('inverter_1','V_In')
	# Stop the simulation.
	# shutdown()
	# proc.kill() # For those hard-to-stop servers.

if __name__ == '__main__':
	_test()