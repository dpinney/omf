''' Utility functions that all models need. '''

import math

def avg(inList):
	''' Average a list. Really wish this was built-in. '''
	return sum(inList)/len(inList)

def hdmAgg(series, func, level):
	''' Simple hour/day/month aggregation for Gridlab. '''
	if level in ['days','months']:
		return util.aggSeries(stamps, series, func, level)
	else:
		return series

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

def pyth(x,y):
	''' Compute the third side of a triangle--BUT KEEP SIGNS THE SAME FOR DG. '''
	fullSign = _sign(_sign(x)*x*x + _sign(y)*y*y)
	return fullSign*math.sqrt(x*x + y*y)

def _sign(z):
	return (-1 if z<0 else 1)

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

def prod(inList):
	''' Product of all values in a list. '''
	return reduce(lambda x,y:x*y, inList, 1)

def vecPyth(vx,vy):
	''' Pythagorean theorem for pairwise elements from two vectors. '''
	rows = zip(vx,vy)
	return map(lambda x:pyth(*x), rows)

def vecSum(*args):
	''' Add n vectors. '''
	return map(sum,zip(*args))

def vecProd(*args):
	''' Multiply n vectors. '''
	return map(prod, zip(*args))

def _pfRow(row):
	''' Power factor calc for one phase. '''
	return math.cos(math.atan((row[0]+row[1]+row[2])/(row[3]+row[4]+row[5])))

def threePhasePowFac(ra,rb,rc,ia,ib,ic):
	''' Get power factor for a row of threephase volts and amps. Gridlab-specific. '''
	rows = zip(ra,rb,rc,ia,ib,ic)
	return map(_pfRow, rows)

def _roundPosSig(y, sig):
	return round(y, sig-int(math.floor(math.log10(y)))-1)

def roundSig(x, sig=3):
	''' Round to a given number of sig figs. '''
	if x == 0: return 0
	elif x < 0: return -1*_roundPosSig(-1*x, sig)
	else: return _roundPosSig(x, sig)

def roundSeries(ser):
	''' Round everythign in a vector to 4 sig figs. '''
	return map(lambda x:roundSig(x,4), ser)

def _tests():
	# TODO: this function.
	pass

if __name__ == '__main__':
	_tests()