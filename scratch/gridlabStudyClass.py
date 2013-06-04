#!/usr/bin/env python

class GridlabStudy:
	analysisName = None
	studyName = None
	studyType = 'gridlabd'
	simLength = None
	simLengthUnits = None
	simStartDate = None
	inputJson = None
	outputJson = None

	def __webInit__(self, studyConfig, inputJson):
		pass

	def __fileInit__(self, jsonDict, jsonMdDict):
		pass

	def __init__(self):
		# Creating a study from web input:
		if jsonDict == []:
			self.inputJson = None
			self.inputJson = None
		# Or we're creating a study from the filesystem:
		else:
			self.analysisName = jsonMdDict['analysisName']
			self.studyName = jsonMdDict['studyName']
			self.simLength = jsonMdDict['simLength']
			self.simLengthUnits = jsonMdDict['simLengthUnits']
			self.simStartDate = jsonMdDict['simLengthUnits']
			self.inputJson = jsonDict['inputJson']
			self.outputJson = jsonDict['outputJson']

	def run(self):
		pass

	def toJson(self):
		pass

def main():
		pass