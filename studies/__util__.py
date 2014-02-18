#!/usr/bin/env python

import math

def _groupBy(inL, func):
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

def aggSeries(timeStamps, timeSeries, func, level):
	''' Aggregate a list + timeStamps up to the required time level. '''
	# Different substring depending on what level we aggregate to:
	if level=='months': endPos = 7
	elif level=='days': endPos = 10
	combo = zip(timeStamps, timeSeries)

	# Group by level:
	groupedCombo = _groupBy(combo, lambda x1,x2: x1[0][0:endPos]==x2[0][0:endPos])
	# Get rid of the timestamps:
	groupedRaw = [[pair[1] for pair in group] for group in groupedCombo]
	return map(func, groupedRaw)

def _sign(z):
	return (-1 if z<0 else 1)

def pyth(x,y):
	''' helper function to compute the third side of the triangle--BUT KEEP SIGNS THE SAME FOR DG '''
	fullSign = _sign(_sign(x)*x*x + _sign(y)*y*y)
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

def _pfRow(row):
	return math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	rows = zip(ra,rb,rc,ia,ib,ic)

	return map(_pfRow, rows)

def roundPosSig(y, sig):
	return round(y, sig-int(math.floor(math.log10(y)))-1)
	
def roundSig(x, sig=3):
	if x == 0: return 0
	elif x < 0: return -1*_roundPosSig(-1*x, sig)
	else: return _roundPosSig(x, sig)

def roundSeries(ser):
	return map(lambda x:roundSig(x,4), ser)

