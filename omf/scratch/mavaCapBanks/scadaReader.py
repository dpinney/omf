'''
Created on Jun 26, 2014
This file reads the scada data from s25-01 Substation load1.csv and to create the various voltage and load player files and calibration criterea.
Then it runs the calibration on the file faNewestConversion.glm using the generated SCADA information and creates the base case.
@author: fish334
'''
import csv
import math
import datetime
import os
import sys
sys.path.append("../../")
import feederCalibrate
import feederPopulate
import feeder
import tempfile
import time

def _readCsv(fcsv):
    f = open(fcsv)
    scadaRow = []
    for row in csv.reader(f):
        scadaRow += [row]
    return scadaRow

def readSCADA(scadaFile):
    scada = {'timestamp' : [],
                    'phaseAW' : [],
                    'phaseBW' : [],
                    'phaseCW' : [],
                    'phaseAVAR' : [],
                    'phaseBVAR' : [],
                    'phaseCVAR' : [],
                    'totalVA' : [],
                    'pfA' : [],
                    'pfB' : [],
                    'pfC' : [],
                    'puLoad' : [],
                    'VoltageA' : [],
                    'VoltageB' : [],
                    'VoltageC' : []}
    scadaInfo = {'summerDay' : None,
                        'winterDay' : None,
                        'shoulderDay' : None,
                        'summerPeakKW' : 0,
                        'summerTotalEnergy' : 30134.0730,
                        'summerPeakHour' : None,
                        'summerMinimumKW' : 1e15,
                        'summerMinimumHour' : None,
                        'winterPeakKW' : 0,
                        'winterTotalEnergy' : 37252.8585,
                        'winterPeakHour' : None,
                        'winterMinimumKW' : 1e15,
                        'winterMinimumHour' : None,
                        'shoulderPeakKW' : 0,
                        'shoulderTotalEnergy' : 38226.7564,
                        'shoulderPeakHour' : None,
                        'shoulderMinimumKW' : 1e15,
                        'shoulderMinimumHour' : None}
    scadaRaw = _readCsv(scadaFile)[1:]
    index = 0
    loadMax = 0.0
    voltA = 120.0
    
    voltB = 120.0
    voltC = 120.0
    for row in scadaRaw:
        if float(row[4]) >= 114.0:
            voltA = float(row[4])
        if float(row[5]) >= 114.0:
            voltB = float(row[5])
        if float(row[6]) >= 114.0:
            voltC = float(row[6])
        scada['timestamp'].append(datetime.datetime.strptime(row[0], "%m/%d/%Y %H:%M"))
        scada['phaseAW'].append(float(row[1])*voltA*7200.0*abs(float(row[7]))/120.0)
        scada['phaseBW'].append(float(row[2])*voltB*7200.0*abs(float(row[8]))/120.0)
        scada['phaseCW'].append(float(row[3])*voltC*7200.0*abs(float(row[9]))/120.0)
        if float(row[7]) >= 0.0:
            scada['phaseAVAR'].append(float(row[1])*voltA*7200.0*math.sqrt(1-(abs(float(row[7])))**2)/120.0)
        else:
            scada['phaseAVAR'].append(-1.0*float(row[1])*voltA*7200.0*math.sqrt(1-(abs(float(row[7])))**2)/120.0)
        if float(row[8]) >= 0.0:
            scada['phaseBVAR'].append(float(row[2])*voltB*7200.0*math.sqrt(1-(abs(float(row[8])))**2)/120.0)
        else:
            scada['phaseBVAR'].append(-1.0*float(row[2])*voltB*7200.0*math.sqrt(1-(abs(float(row[8])))**2)/120.0)
        if float(row[9]) >= 0.0:
            scada['phaseCVAR'].append(float(row[3])*voltC*7200.0*math.sqrt(1-(abs(float(row[9])))**2)/120.0)
        else:
            scada['phaseCVAR'].append(-1.0*float(row[3])*voltC*7200.0*math.sqrt(1-(abs(float(row[9])))**2)/120.0)
        scada['pfA'].append(float(row[7]))
        scada['pfB'].append(float(row[8]))
        scada['pfC'].append(float(row[9]))
        scada['VoltageA'].append(str(complex(voltA*7200.0/120.0, 0.0)).replace('(','').replace(')',''))
        scada['VoltageB'].append(str(complex(-voltB*7200.0*0.5/120.0, -voltB*7200.0*math.sqrt(3)*0.5/120.0)).replace('(','').replace(')',''))
        scada['VoltageC'].append(str(complex(-voltC*7200.0*0.5/120.0, voltC*7200.0*math.sqrt(3)*0.5/120.0)).replace('(','').replace(')',''))
        scada['totalVA'].append(complex(scada['phaseAW'][index] + scada['phaseBW'][index] + scada['phaseCW'][index], scada['phaseAVAR'][index] + scada['phaseBVAR'][index] + scada['phaseCVAR'][index]))
        if scada['timestamp'][index].year == 2013:
            if scada['timestamp'][index].month in [1, 2, 12]:
                if scadaInfo['winterPeakKW'] < scada['totalVA'][index].real/1000.0:
                    scadaInfo['winterPeakKW'] = scada['totalVA'][index].real/1000.0
                    scadaInfo['winterDay'] = scada['timestamp'][index].strftime("%Y-%m-%d")
                    scadaInfo['winterPeakHour'] = float(scada['timestamp'][index].hour) + (int(scada['timestamp'][index].minute)/60.0)
            elif scada['timestamp'][index].month in [3, 4, 5, 9, 10, 11]:
                if scadaInfo['shoulderPeakKW'] < scada['totalVA'][index].real/1000.0:
                    scadaInfo['shoulderPeakKW'] = scada['totalVA'][index].real/1000.0
                    scadaInfo['shoulderDay'] = scada['timestamp'][index].strftime("%Y-%m-%d")
                    scadaInfo['shoulderPeakHour'] = float(scada['timestamp'][index].hour) + (int(scada['timestamp'][index].minute)/60.0)
            elif scada['timestamp'][index].month in [6, 7 , 8]:
                if scadaInfo['summerPeakKW'] < scada['totalVA'][index].real/1000.0:
                    scadaInfo['summerPeakKW'] = scada['totalVA'][index].real/1000.0
                    scadaInfo['summerDay'] = scada['timestamp'][index].strftime("%Y-%m-%d")
                    scadaInfo['summerPeakHour'] = float(scada['timestamp'][index].hour) + (int(scada['timestamp'][index].minute)/60.0)
            if loadMax <= abs(scada['totalVA'][index]):
                loadMax = abs(scada['totalVA'][index])
        index += 1
    for load in scada['totalVA']:
        scada['puLoad'].append(abs(load)/loadMax)
    for index in xrange(len(scada['timestamp'])):
        if scadaInfo['winterDay'] == scada['timestamp'][index].strftime("%Y-%m-%d") and scadaInfo['winterMinimumKW'] > scada['totalVA'][index].real/1000.0 and scada['totalVA'][index] != 0.0:
            scadaInfo['winterMinimumKW'] = scada['totalVA'][index].real/1000.0
            scadaInfo['winterMinimumHour'] = float(scada['timestamp'][index].hour) + (int(scada['timestamp'][index].minute)/60.0)
        if scadaInfo['summerDay'] == scada['timestamp'][index].strftime("%Y-%m-%d") and scadaInfo['summerMinimumKW'] > scada['totalVA'][index].real/1000.0 and scada['totalVA'][index] != 0.0:
            scadaInfo['summerMinimumKW'] = scada['totalVA'][index].real/1000.0
            scadaInfo['summerMinimumHour'] = float(scada['timestamp'][index].hour) + (int(scada['timestamp'][index].minute)/60.0)
        if scadaInfo['shoulderDay'] == scada['timestamp'][index].strftime("%Y-%m-%d") and scadaInfo['shoulderMinimumKW'] > scada['totalVA'][index].real/1000.0 and scada['totalVA'][index] != 0.0:
            scadaInfo['shoulderMinimumKW'] = scada['totalVA'][index].real/1000.0
            scadaInfo['shoulderMinimumHour'] = float(scada['timestamp'][index].hour) + (int(scada['timestamp'][index].minute)/60.0)
    for key in scadaInfo.keys():
        print key, scadaInfo[key]
    loadShapeFile = open('./loadShapeScalar.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['puLoad'][index]))
    loadShapeFile.close()
    loadShapeFile = open('./phaseApf.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfA'][index]))
    loadShapeFile.close()
    loadShapeFile = open('./phaseBpf.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfB'][index]))
    loadShapeFile.close()
    loadShapeFile = open('./phaseCpf.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:0.6f}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['pfC'][index]))
    loadShapeFile.close()
    loadShapeFile = open('./phaseAVoltage.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageA'][index]))
    loadShapeFile.close()
    loadShapeFile = open('./phaseBVoltage.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageB'][index]))
    loadShapeFile.close()
    loadShapeFile = open('./phaseCVoltage.player', 'w')
    for index in xrange(len(scada['timestamp'])):
        if scada['puLoad'][index] != 0.0:
            if scada['timestamp'][index].month in [1, 2, 12]:
                loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
            elif scada['timestamp'][index].month in [4, 5, 6, 7, 8, 9, 10]:
                loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
            elif scada['timestamp'][index].month == 3:
                if scada['timestamp'][index].day < 10:
                    loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
                elif scada['timestamp'][index].day > 10:
                    loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
                elif scada['timestamp'][index].day == 10:
                    if scada['timestamp'][index].hour < 2:
                        loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
                    elif scada['timestamp'][index].hour > 2:
                        loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
            elif scada['timestamp'][index].month == 11:
                if scada['timestamp'][index].day < 3:
                    loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
                elif scada['timestamp'][index].day > 3:
                    loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
                elif scada['timestamp'][index].day == 3:
                    if index < 29380:
                        loadShapeFile.write('{:s} CDT,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
                    else:
                        loadShapeFile.write('{:s} CST,{:s}\n'.format(scada['timestamp'][index].strftime("%Y-%m-%d %H:%M:%S"), scada['VoltageC'][index]))
    loadShapeFile.close()
    configInfo= {'timezone' : 'CST+6CDT',
        'startdate' : '2013-01-01 0:00:00',
        'stopdate' : '2014-01-01 0:00:00',
        'feeder_rating' : loadMax*1.15,
        'nom_volt' : 7200,
        'voltage_players' : [os.path.abspath('./phaseAVoltage.player').replace('\\', '/'), os.path.abspath('./phaseBVoltage.player').replace('\\', '/'), os.path.abspath('./phaseCVoltage.player').replace('\\', '/')],
        'load_shape_scalar' : 1.0,
        'r_p_pfA' : os.path.abspath('./phaseApf.player').replace('\\', '/'),
        'r_p_pfB' : os.path.abspath('./phaseBpf.player').replace('\\', '/'),
        'r_p_pfC' : os.path.abspath('./phaseCpf.player').replace('\\', '/'),
        'load_shape_player_file' : os.path.abspath('./loadShapeScalar.player').replace('\\', '/')}
    working_directory = tempfile.mkdtemp()
    feederTree = feeder.parse('./faNewestConversionNoRecorder.glm')
    calibratedFeederTree, calibrationConfiguration = feederCalibrate.startCalibration(working_directory, feederTree, scadaInfo, 'MavaCapBank', configInfo)
    print(calibrationConfiguration['load_shape_scalar'])
    calibratedFile = open('./mavaCapBanksBaseCase.glm', 'w')
    glmstring = feeder.sortedWrite(calibratedFeederTree)
    calibratedFile.write(glmstring)
    calibratedFile.close()
#     calibratedFeeder, last_key =  feederPopulate.startPopulation(feederTree,-1,configInfo)
#     calibratedFile = open('./mavaCapBanksRaw.glm', 'w')
#     glmstring = feeder.sortedWrite(calibratedFeeder)
#     calibratedFile.write(glmstring)
#     calibratedFile.close()
if __name__ == '__main__':
    startCPU = time.clock()
    scadaInfo = readSCADA('./s25-01 Substation load1.csv')
    endCPU = time.clock()
    timeDiff = endCPU - startCPU
    hour = math.floor(timeDiff/3600.0)
    minute = math.floor((timeDiff - (hour*3600.0))/60.0)
    sec = int(timeDiff - (hour*3600.0) - (minute*60.0))
    print("{:d}h {:d}m {:d}s".format(int(hour), int(minute), sec))