import os, urllib, urllib2, subprocess, time, warnings, webbrowser
from datetime import datetime, timedelta

def parseDt(dtString):
	'Parse GridLAB-D date time strings'
	return datetime.strptime(dtString, "%Y-%m-%d %H:%M:%S")

def writeDt(dtString):
	'Write GridLAB-D date time strings.'
	return datetime.strftime(dtString, "%Y-%m-%d %H:%M:%S")

class Coordinator(object):
	__slots__ = 'agents', 'glw', 'log'

	def __init__(self, agents, cosimProps):
		self.agents = agents
		# Start the simulation
		self.glw = GridLabWorld(cosimProps['port'],cosimProps['hostname'],cosimProps['glmPath'],cosimProps['startTime'])
		self.glw.start()
		# Make a list of all the timesteps we are communicating on.
		startDt = parseDt(cosimProps['startTime'])
		endDt = parseDt(cosimProps['endTime'])
		stepDelta = timedelta(seconds=cosimProps['stepSizeSeconds'])
		stepNum = (endDt - startDt).total_seconds() / cosimProps['stepSizeSeconds']
		stepDts = [startDt + stepDelta * x  for x in range(int(stepNum))]
		# Initialize the log.
		self.log = []
		# Step through each time step.
		for now in stepDts:
			logEntry = [now]
			# At each time step each agent acts.
			for a in agents:
				# Send agent's request to GridLAB-D
				nowStr = writeDt(now)
				readRequests = a.readStep(nowStr)
				readResults = self.glw.doRequests(readRequests)
				logEntry.append([readRequests, readResults])
				# Send results from GridLAB-D back to agent for write step.
				writeCommands = a.writeStep(nowStr, readResults)
				writeResults = self.glw.doRequests(writeCommands)
				logEntry.append([writeCommands,writeResults])
			self.log.append(logEntry)
			self.glw.waitUntil(writeDt(now + stepDelta))

	def drawResults(self):
		#return self.log
		html_str = """
		<!DOCTYPE html>
		<html>
			<head>
				<style>
					table, th, td { border: 1px solid black; 
					text-align: center;}
				</style>
			</head>
			<body>
				<table>
					<tr>
						<th>Time</th>"""
						
		for x in range(len(self.agents)):
			temp_str = "<th>Agent"+str(x)+"_Read</th><th>Agent"+str(x)+"_ReadRes</th><th>Agent"+str(x)+"_Write</th><th>Agent"+str(x)+"_WriteRes</th>"
			html_str += temp_str
		html_str += """
					</tr>"""
		for row in self.log:
			row_str = "<tr><td>"+row.pop(0).strftime("%Y-%m-%d %H:%M:%S")+"</td>"
			for col in row:
				row_str += "<td>"+str(col[0])+"</td><td>"+str(col[1])+"</td>"
			row_str += "</tr>"
			html_str += row_str
		html_str += """
				</table>
			</body>
		</html>"""
		Html_file = open("output.html", "w")
		Html_file.write(html_str)
		Html_file.close()

class GridLabWorld(object):
	__slots__ = 'PORT', 'HOST', 'GLM_PATH', 'START_PAUSE', 'baseUrl'

	def __init__(self, PORT, HOST, GLM_PATH, START_PAUSE):
		self.PORT = PORT
		self.HOST = HOST
		self.GLM_PATH = GLM_PATH
		self.START_PAUSE = START_PAUSE
		# Derived global.
		self.baseUrl = 'http://' + HOST + ':' + PORT + '/'

	def doRequests(self, reqList):
		'Do multiple requests.'
		# E.g. reqList = [{'cmd':'readClock|read|write', 'obName':'', 'propName':'', 'value':''}]
		results = []
		for req in reqList:
			reqType = req.get('cmd','')
			obName = req.get('obName', '')
			propName = req.get('propName', '')
			value = req.get('value', '')
			if reqType == 'readClock':
				results.append(self.readClock())
			elif reqType == 'read':
				results.append(self.read(obName, propName))
			elif reqType == 'write':
				results.append(self.write(obName, propName, value))
		return results

	def waitUntil(self, targetTime):
		'Step to targetTime in current simulation.'
		try:
			# HACK: we don't need full URL encoding right?
			niceUrl = self.baseUrl + 'control/pauseat=' + targetTime.replace(' ','%20')
			urllib2.urlopen(niceUrl).read()
			currentTime = None
			while currentTime != targetTime:
				time.sleep(0.2)
				#HACK: Read clock and also drop the timezone because it causes problems.
				currentTime = urllib2.urlopen(self.baseUrl + 'raw/clock').read()[0:-4]
		except:
			warnings.warn("Wait until " + targetTime + " failed!")

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
	print '* Bunch of requests:', glw.doRequests([{'cmd':'read', 'obName':'solar_1', 'propName':'V_Out'},{'cmd':'readClock'}])
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

def _test2():
	# test with AlertAgent, ReadAttackAgent
	import cyberAttack
	cosimProps = {'port':'6267', 'hostname':'localhost', 'glmPath':'./smsSingle.glm', 'startTime':'2000-01-01 00:00:00','endTime':'2000-01-05 12:00:00', 'stepSizeSeconds':3600} #error with having 
	agents = [cyberAttack.AlertAgent('2000-01-03 12:00:00')] 
	print 'Starting co-sim with 1 agent.'
	coord = Coordinator(agents, cosimProps)
	# print coord.drawResults()

def _test3():
	# test with AlertAgent, ReadAttackAgent
	import cyberAttack
	cosimProps = {'port':'6267', 'hostname':'localhost', 'glmPath':'./smsSingle.glm', 'startTime':'2000-01-01 00:00:00','endTime':'2000-01-05 00:00:00', 'stepSizeSeconds':3600}
	agents = [cyberAttack.AlertAgent('2000-01-03 12:00:00'), cyberAttack.ReadAttackAgent('2000-01-02 10:00:00', 'tm_1', 'measured_power')]
	print 'Starting co-sim with 2 agents.'
	coord = Coordinator(agents, cosimProps)
	print coord.drawResults()

def _test4():
	# test with AlertAgent, ReadAttackAgent, and ReadAttackIntervalAgent
	import cyberAttack
	cosimProps = {'port':'6267', 'hostname':'localhost', 'glmPath':'./smsSingle.glm', 'startTime':'2000-01-01 00:00:00','endTime':'2000-01-05 00:00:00', 'stepSizeSeconds':3600}
	agents = [cyberAttack.AlertAgent('2000-01-03 04:00:00'), cyberAttack.ReadAttackAgent('2000-01-02 10:00:00', 'tm_1', 'measured_power'), cyberAttack.ReadIntervalAttackAgent('2000-01-02 08:00:00', '2000-01-03 08:00:00', 'tm_1', 'measured_real_energy')]
	print 'Starting co-sim with 3 agents.'
	coord = Coordinator(agents, cosimProps)
	print coord.drawResults()

def _test5():
	# test with AlertAgent, ReadAttackAgent, ReadIntervalAttackAgent, and WriteAttackAgent
	#shows how WriteAttackAgent and WriteIntervalAttackAgent interact with ReadAttackAgent and ReadIntervalAttackAgent
	import cyberAttack
	cosimProps = {'port':'6267', 'hostname':'localhost', 'glmPath':'./smsSingle.glm', 'startTime':'2000-01-01 00:00:00','endTime':'2000-01-05 00:00:00', 'stepSizeSeconds':3600}
	agents = []
	agents.append(cyberAttack.AlertAgent('2000-01-03 04:00:00'))
	agents.append(cyberAttack.ReadAttackAgent('2000-01-02 10:00:00', 'tm_1', 'measured_power'))
	agents.append(cyberAttack.ReadIntervalAttackAgent('2000-01-02 08:00:00', '2000-01-03 08:00:00', 'tm_1', 'measured_real_energy'))
	agents.append(cyberAttack.WriteAttackAgent('2000-01-02 16:00:00', 'tm_1', 'measured_real_energy', '0.0'))
	agents.append(cyberAttack.WriteIntervalAttackAgent('2000-01-03 20:00:00', '2000-01-04 08:00:00', 'inverter_1', 'power_factor', '0.4'))
	agents.append(cyberAttack.ReadIntervalAttackAgent('2000-01-03 12:00:00', '2000-01-04 12:00:00', 'tm_2', 'measured_reactive_power'))
	agents.append(cyberAttack.DefendByValueAgent('battery_1', 'generator_status', 'ONLINE'))
	agents.append(cyberAttack.WriteAttackAgent('2000-01-01 04:00:00', 'battery_1', 'generator_status', 'OFFLINE'))
	print 'Starting co-sim with 8 agents.'
	coord = Coordinator(agents, cosimProps)
	print coord.drawResults()

if __name__ == '__main__':
	_test5()