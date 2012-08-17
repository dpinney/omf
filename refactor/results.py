#!/usr/bin/env python

import os
import utility
import matplotlib as m
m.use('Agg')
import matplotlib.pyplot as p

class Results:
	''' recorders = {csvName:{columnName:[]},...}'''
	recorders = None

	def __init__(self, csvStringDict=None, directory=None):
		self.recorders = {}
		# If we got a directory, get everything from there:
		if directory != None:
			csvDict = {}
			for fileName in os.listdir(directory):
				if fileName.endswith('.csv'):
					with open(directory + fileName, 'r') as openFile:
						self.recorders[fileName] = self.csvStringToRecorder(openFile.read())
		# Otherwise, walk the csv strings:
		else:
			for csv in csvStringDict:
				self.recorders[csv] = self.csvStringToRecorder(csvStringDict[csv])

	def csvStringToRecorder(self, csvString):
		# Helper function that translates csv values to reasonable floats (or header values to strings):
		def strClean(x):
			if x == 'OPEN':
				return 1.0
			elif x == 'CLOSED':
				return 0.0
			elif x[0] == '+':
				return float(x[1:])
			elif x[0] == '-':
				return float(x)
			elif x[0].isdigit() and x[-1].isdigit():
				return float(x)
			else:
				return x
		outDict = {}
		lines = csvString.splitlines()
		array = map(lambda x:x.split(','), lines)
		cleanArray = [map(strClean, x) for x in array]
		# Magic number 8 is the number of header rows in each csv.
		arrayNoHeaders = cleanArray[8:]
		# Drop the timestamp column:
		trimmedArray = [line[1:] for line in arrayNoHeaders]
		# transpose the matrix:
		timeSeriesList = zip(*trimmedArray)
		for x in timeSeriesList:
			outDict[x[0]] = x[1:]
		return outDict

	def isSane(self):
		'''Makes sure all the recorder time series are the same length'''
		leng = 0
		for key in self.recorders:
			for key2 in self.recorders[key]:
				datum = self.recorders[key][key2]
				if leng == 0:
					leng = len(datum)
				elif len(datum) != leng:
					# Dimensional mismatch!
					return False
		return True

	def crossProd(self, realVec,imVec):
		return map(lambda x:math.sqrt(x[0]*x[0]+x[1]*x[1]), zip(realVec, imVec))

	def graphRecorder(self, recorder):
		fig = p.figure()
		for key in recorder:
			p.plot(recorder[key], label=key)
		p.legend()
		return fig

def main():
	'''tests go here.'''
	testDir = '../static/analyses/again/'
	test = Results(directory=testDir)
	print test.recorders.keys()
	print test.recorders['Regulator_Reg1.csv'].keys()
	print 'Sane? ' + str(test.isSane())
	print utility.printNestDicts(test.recorders)
	print os.getcwd()
	# fig = test.graphRecorder(test.recorders['Voltage_630.csv']).savefig('test.png')

if __name__ == '__main__':
	main()