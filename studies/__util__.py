#!/usr/bin/env python

import math

def aggSeries(timeStamps, timeSeries, func, level):
	''' Aggregate a list + timeStamps up to the required time level. '''
	# Different substring depending on what level we aggregate to:
	if level=='months': endPos = 7
	elif level=='days': endPos = 10
	combo = zip(timeStamps, timeSeries)
	def groupBy(inL, func):
		''' Take a list and func, and group items in place comparing with func. Make sure the func is an equivalence relation, or your brain will hurt. '''
		if inL == []: return inL
		if len(inL) == 1: return [inL]
		newL = [[inL[0]]]
		for item in inL[1:]:
			if func(item, newL[-1][0]):
				newL[-1].append(item)
			else:
				newL.append([item])
		return newL	
	# Group by level:
	groupedCombo = groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return map(func, groupedRaw)

def pyth(x,y):
	''' helper function to compute the third side of the triangle--BUT KEEP SIGNS THE SAME FOR DG '''
	def sign(z):
		return (-1 if z<0 else 1)
	fullSign = sign(sign(x)*x*x + sign(y)*y*y)
	return fullSign*math.sqrt(x*x + y*y)

def prod(inList):
	return reduce(lambda x,y:x*y, inList, 1)

def vecPyth(vx,vy):
	rows = zip(vx,vy)
	return map(lambda x:pyth(*x), rows)

def vecSum(*args):
	return map(sum,zip(*args))

def vecProd(*args):
	return map(prod, zip(*args))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	rows = zip(ra,rb,rc,ia,ib,ic)
	def pfRow(row):
		return math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))
	return map(pfRow, rows)

def roundSig(x, sig=3):
	def roundPosSig(y):
		return round(y, sig-int(math.floor(math.log10(y)))-1)
	if x == 0: return 0
	elif x < 0: return -1*roundPosSig(-1*x)
	else: return roundPosSig(x)

def roundSeries(ser):
	return map(lambda x:roundSig(x,4), ser)

