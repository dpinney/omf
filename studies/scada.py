#!/usr/bin/env python

#===============================================================================
# SCADA power date reader. Form columns: feeder, location, time, KW, KVAR, etc.
#===============================================================================
__author__ = "Hongwei Jin"
__copyright__ = "Copyright 2013, CRN @ NRECA"
__status__ = "Developing"

import csv, re, json, StringIO
from datetime import datetime
from datetime import timedelta

with open('./studies/scada.html','r') as configFile: configHtmlTemplate = configFile.read()

class Scada:
	"""
		
	"""
	scada_dict = {}
	fieldnames = {}
	# time_header = ''
	# meterID_header = ''
	# KW_header = ''
	def __init__(self, jsonDict, new = False):
		"""
			Initilize the variables
		"""
		self.analysisName = jsonDict.get('analysisName','')
		self.name = jsonDict.get('name','')
		self.simLength = jsonDict.get('simLength',0)
		self.simLengthUnits = jsonDict.get('simLengthUnits','')
		self.simStartDate = jsonDict.get('simStartDate','')
		self.inputJson = jsonDict.get('inputJson', {})
		self.outputJson = jsonDict.get('outputJson', {})
		# self.sourceFeeder = jsonDict.get('sourceFeeder', '')
		self.sourceFeeder = 'N/A'
		self.climate = jsonDict.get('climate', '')
		self.studyType = 'scada'

	def run(self):
		"""
			For those who doesn't match the timestamps provide in the glb simulation, put 'NaN' to the list.
			return the power data list
		"""
		# Handle the header
		try:
			self.scada_dict = {}
			blah = self.inputJson['hiddenScadaFile'].encode('ascii')
			csvString = StringIO.StringIO(blah)
			reader = csv.DictReader(csvString)
			fields = reader.fieldnames
			# get rid of spaces. Pre process the headers
			for field in fields:
				if field.startswith('KW('):
					self.fieldnames['KW_header'] = field.strip()
				elif field.startswith('Date'):
					self.fieldnames['time_header'] = field.strip()
				elif field.startswith('Meter'):
					self.fieldnames['meterID_header'] = field.strip()
				self.scada_dict[field.strip()] = []
			for line in reader:
				for field in fields:
					self.scada_dict[field.strip()].append(line[field].strip())
			# set power_list null for highcharts
			power_list = [None]
			power_list = power_list * self.simLength
			cleanOut = {}
			simTimestamps = self.dealingTimestamps()
			timeList = self.getTime()
			[tIndex, offset] = self.matchTime(timeList, simTimestamps)

			if tIndex == None and offset == None:
				# Timestamps not match
				stdoutwarning = 'TimeStamps not match at all, please choose another scada file.'
				return False
			else:
				KWList = self.getKW(tIndex, self.simLength - offset)
				endpoint = self.simLength if offset+len(KWList)>self.simLength else offset+len(KWList)
				power_list[offset:endpoint] = KWList

			# dump data into standard json file.
			cleanOut['Consumption'] = {}
			cleanOut['Consumption']['Power'] = power_list
			
			# TODO:
			# timeStamps
			def timeStamps(simList):
			    newList = []
			    for time in simList:
			        new = time.strftime('%Y-%m-%d %H:%M:%S'+' PDT')
			        newList.append(new)
			    return newList
			cleanOut['timeStamps'] = timeStamps(simTimestamps)
			cleanOut['Climate'] = {}

			# timestamps completely match or partially match
			stdout = 'Succeed in matching time stamps' 
			cleanOut['stdout'] = stdout
			cleanOut['stderr'] = ''
			cleanOut['componentNames'] = []
			self.outputJson = cleanOut
			return True
		except:
			return False
			raise Exception
	def dealingTimestamps(self):
		"""
			Create a list of datetime object according to list
		"""
		start_time = datetime.strptime(self.simStartDate, '%Y-%m-%d')
		t_Stamps = []
		for i in range(self.simLength):
			if self.simLengthUnits == 'hours':
				t_Stamps.append(start_time + timedelta(hours=1 * i))
			elif self.simLengthUnits == 'minutes':
				t_Stamps.append(start_time + timedelta(minutes=1 * i))
			elif self.simLengthUnits == 'days':
				t_Stamps.append(start_time + timedelta(days=1 * i))
		return t_Stamps
	
	def getMeterID(self):
		"""
			Read meter ID from .csv file. 
			Return list object.
		"""
		if self.fieldnames['meterID_header'] != '':
			return self.scada_dict[self.fieldnames['meterID_header']]
		else:
			return None
		
	def getTime(self):
		"""
			Read date and time from .csv file, convert them to datetime objects.
			Return datetime object list.
		"""
		if self.fieldnames['time_header'] != '':
			timeList = self.scada_dict[self.fieldnames['time_header']]
			newList = []
			for time in timeList:
				date_object = datetime.strptime(time, '%m/%d/%Y %H:%M')
				newList.append(date_object)
			# update the scada_dict
			# self.scada_dict['Date / Time'] = newList
			return newList
		else:
			return None
	
	def matchTime(self, timeList, simTimestamps):
		"""
			Match timestamps by detecting minutes, hours, days.
			return matched timestamps index, simTimestamps offset from beginning.
			----------------				------------   	<- timeList
			   ~~~~~~~~~~~~~			~~~~~~~~~~~~~~~~	<- simTimestamps
			   | index						| offset
		"""
		def matchToMinute():
			for t in timeList:
				if t.month == first_sim_timestamp.month and t.day == first_sim_timestamp.day and t.hour == first_sim_timestamp.hour and t.minute == first_sim_timestamp.minute:
					return timeList.index(t), 0
				else:
					continue 
				
			for n in simTimestamps:
				if n.month == first_scada_timestamp.month and n.day == first_scada_timestamp.day and n.hour == first_scada_timestamp.hour and n.minute == first_scada_timestamp.minute:
					return 0, simTimestamps.index(n)
				else:
					continue
			# for not matched at all
			return None, None
		
		def matchToHour():
			for t in timeList:
				if t.month == first_sim_timestamp.month and t.day == first_sim_timestamp.day and t.hour == first_sim_timestamp.hour:
					return timeList.index(t), 0
				else:
					continue 
				
			for n in simTimestamps:
				if n.month == first_scada_timestamp.month and n.day == first_scada_timestamp.day and n.hour == first_scada_timestamp.hour:
					return 0, simTimestamps.index(n)
				else:
					continue
			# for not matched at all
			return None, None
		
		def matchToDay():
			for t in timeList:
				if t.month == first_sim_timestamp.month and t.day == first_sim_timestamp.day:
					return timeList.index(t), 0
				else:
					continue 
				
			for n in simTimestamps:
				if n.month == first_scada_timestamp.month and n.day == first_scada_timestamp.day:
					return 0, simTimestamps.index(n)
				else:
					continue
			# for not matched at all
			return None, None

		first_sim_timestamp = simTimestamps[0]
		first_scada_timestamp = timeList[0]
		# TODO: detect yearly looped timeList
		if self.simLengthUnits == 'minutes':
			return matchToMinute()
		elif self.simLengthUnits == 'hours':
			return matchToHour()
		elif self.simLengthUnits == 'days':
			return matchToDay()

	def getKW(self, tIndex, size):
		"""
			Read KW data from .csv file, convert them to float type.
			Return float list.
		"""
		def KWByMinute(tIndex, size):
			newList = []
			run = (size / 60 +1) if (size/60+1)<(len(KWList)-tIndex) else (len(KWList)-tIndex)
			for t in range(run):
				for i in (range(60 if size >= 60 else size % 60)):
					newList.append(round(KWList[tIndex + t] + i * (KWList[tIndex + 1 + t] - KWList[tIndex + t]) / 60, 2))
				size -= 60
			return newList

		def KWByHour(tIndex, size):
			size = size if size < len(KWList)-tIndex else len(KWList)-tIndex
			return KWList[tIndex: tIndex + size]

		def KWByDay(tIndex, size):
			newList = []
			sum = 0
			aver = 0
			size = size if size < (len(KWList)-tIndex)/24 else (len(KWList)-tIndex)/24
			for t in range(size):
				for i in range(24):
					sum += KWList[tIndex + t + i]
					aver = sum / 24
				newList.append(round(aver, 2))
				sum = 0
				aver = 0
			return newList
			
		if self.fieldnames['KW_header'] != '':
			KWList = self.scada_dict[self.fieldnames['KW_header']]
			for i in range(len(KWList)):
				KWList[i] = float(KWList[i]) * 1000
			# update the scada_dict
			self.scada_dict[self.fieldnames['KW_header']] = KWList
			# return KWList
		
		if self.simLengthUnits == 'minutes':
			return KWByMinute(tIndex, size)
		elif self.simLengthUnits == 'hours':
			return KWByHour(tIndex, size)
		elif self.simLengthUnits == 'days':
			return KWByDay(tIndex, size)

	# idle function
	def getKVAR(self):
		"""
			Read KVAR from .csv file, convert them to float type.
			Return float list.
		"""
		if self.KVAR_header != '':
			KVARList = self.scada_dict[self.KVAR_header]
			for i in range(len(KVARList)):
				KVARList[i] = float(KVARList[i])
			self.scada_dict[self.KVAR_header] = KVARList
			return KVARList
		else:
			None

	# idle function
	def getKVA(self):
		"""
			Read KVA from .csv file, convert them to float type:
			Return float list.
		"""
		# TODO:
		if self.KVA_header != '':
			KVAList = self.scada_dict[self.KVA_header]
			for i in range(len(KVAList)):
				KVAList[i] = float(KVAList[i])
			self.scada_dict[self.KVA_header]
			return KVAList
		else: 
			None 
	
	# idle function
	def getKVARE(self):
		"""
			Read KVARE from .csv file. convert to float type:
			Return float list.
		"""
		if self.KVARE_header != '':
			return 'test'
		else:
			return None

	
	# idle function
	def getPF(self):
		return self.scada_dict[self.PF_header]
	
	# idle function
	def getLen(self):
		return len(self.scada_dict.meterID_header)
	
	# idle function
	def getKeys(self):
		return self.scada_dict.keys()

if __name__ == '__main__':
	"""
		test code
	"""
	analysis_name = 'ACEC for NRECA'
	file_prefix = './uploads/'

	analysis_file_prefix = './data/Analysis/' + analysis_name
	s = scada(file_prefix+'ACEC Total.csv', analysis_file_prefix+'.json')
	# with open('test.txt', 'w') as file:
	#     file.write(str(s.run()))
	print s.run()
#     s.run()
