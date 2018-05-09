import cosim

class ShutdownAgent(object):
	shutDownTime = "2012-00-03 12:00:00" # Default!
	
	def __init__(self, shutDownTime):
		self.shutDownTime = shutDownTime

	def req(self, time):
		if time == self.shutDownTime:
			return [{}]

	def feedback(self, time, rezList):
		if {'writeStatus':'success'} in rezList:
			print 'Success!'


class DefendOutput(object):
	obNameToDefend = "Test_inverter_1" # Default!
	obPropToDefend = "V_Out" # Default!
	propTarget = "3.0" # Default!
	defenseQueue = []

	def __init__(self, obNameToDefend, obPropToDefend, propTarget):
		self.obNameToDefend = obNameToDefend
		self.obPropToDefend = obPropToDefend
		self.propTarget = propTarget

	def req(self, time):
		payload = defenseQueue + [{'cmd':'read','object':self.obNameToDefend,'prop':self.obPropToDefend}]
		self.defenseQueue = []
		return payload

	def feedback(self, time, rezList):
		for message in rezList:
			if message.get('val') < self.propTarget:
				self.defenseQueue.append({'cmd':'write','object':self.obNameToDefend,'prop':self.obPropToDefend,'val':self.propTarget})