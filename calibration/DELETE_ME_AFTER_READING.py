''' Example on how to import feeder.py when working in the calibration folder. '''

import sys
sys.path.append('..')
import feeder

print 'Here are all the function defined in feeder', dir(feeder)