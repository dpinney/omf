class AlertAgent(object):
	__slots__ = 'alertTime'
	# e.g. "2012-00-03 12:00:00"
	
	def __init__(self, alertTime):
		self.alertTime = alertTime

	def readStep(self, time):
		return []

	def writeStep(self, time, rezList):
		if time == self.alertTime:
			print '!!!!!Alerting because it is now ', self.alertTime, '!!!!!!!'
		return []

class DefendOutput(object):
	__slots__ = 'obNameToDefend', 'obPropToDefend', 'propTarget'
	# e.g. "Test_inverter_1", "V_Out", "3.0"

	def __init__(self, obNameToDefend, obPropToDefend, propTarget):
		self.obNameToDefend = obNameToDefend
		self.obPropToDefend = obPropToDefend
		self.propTarget = propTarget

	def readStep(self, time):
		return [] # Doesn't need to read.

	def writeStep(self, time, rezList):
		return [{'cmd':'write','object':self.obNameToDefend,'prop':self.obPropToDefend,'val':self.propTarget}]