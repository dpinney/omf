'''
This script creates hourly price points for reserve pricing for different energy markets in the USA. Price data outlined in
Argonne National Laboratory 'Survey of US Ancillary Services Markets' ANL/ESD-16/1 prepared by Zhi Zhou, Todd Levin, and Guenter Conzelmann.
January 2016 
''' 

from scipy.stats import truncnorm
from random import randint 
import math
import pandas as pd

# Format for market parameters: min, mean, max, stdev, %chance price point is 0 all in $/MWh

# Regulation Parameters
ERCOT_reg_up =    [1.00, 12.48, 4999, 61.95, 0.0]
ERCOT_reg_down =  [0.5, 9.77, 310.08, 13.23, 0.0]
MISO_reg =        [2.5, 11.24, 202.39, 6.43, 0.0]
NYSIO_E_reg =     [0.71, 13.76, 408.13, 26.08, 0.0]
NYISO_W_reg =     [0.71, 13.76, 408.13, 26.08, 0.0]
PJM_reg =         [0.01, 43.70, 3303.87, 104.07, 0.0]
SPP_UP_reg =      [1.36, 14.88, 125.9, 8.42, 0.0]
SPP_DOWN_reg =    [0.07, 7.70, 294.09, 6.05, 0.0]
CAISO_UP_reg =    [0.09, 5.41, 50.01, 5.50, 0.0]
CAISO_DOWN_reg =  [0.00, 3.90, 59.55, 2.62, 4.4]

# Spinning Parameters
CAISO_EXP_spin = [0.09, 3.34, 46.29, 5.13, 0.0]
ERCOT_spin = [2, 14.15, 1285.73, 31.82, 0.0]
MISO_spin = [0.45, 2.58, 88.62, 3.31, 0.0]
ISONE_spin = [0.00, 2.53, 1000, 22.57, 82.7]
NYISO_W_spin = [0.00, 4.07, 650.78, 23.21, 69.3]
NYISO_E_spin = [0.00, 6.49, 964.31, 33.45, 87.6]
PJM_synch = [0.00, 4.21, 1142.35, 32.55, 62.6]
SPP_spin = [0.01, 7.46, 103.72, 6.67, 0.0]

# Non-Spinning Parameters
CAISO_EXP_nospin = [0.08, 0.14, 23.06, 0.61, 0.0]
ERCOT_nospin = [0.77, 5.48, 435.70, 14.03, 0.0]
MISO_supplemental = [0.45, 1.35, 87.95, 2.96, 0.0]
ISONE_nospin =[0.00, 1.62, 1000, 21.99, 97.8]
ISONE_operating = [0.00, 1.6, 1000, 20.62, 97.8]
NYISO_E_nospin = [0.00, 1.75, 891.03, 24.13, 98.2]
NYISO_W_nospin = [0.00, 0.49, 445.34, 10.62, 99.5]
NYISO_E_reserve30 = [0.00, 0.12, 246.98, 4.37, 99.9]
NYISO_W_reserve30 = [0.00, 0.10, 234.4, 3.89, 99.9]
PJM_primary = [0.00, 0.95, 400, 13.32, 95.5]
SPP_supplemental = [0.01, 1.82, 98, 2.2, 0.0]

class distTruncRandNorm:
	''' Class for defining a truncated random normal distribution. '''
	def __init__(self, array):
		self.array = array
	def get_truncated_normal(self, mean=0, sd=1, low=0, upp=10):
		return truncnorm((low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)
	def samplesAnnualHourly(self):
		min_val = self.array[0]
		mean = self.array[1]
		max_val = self.array[2]
		stdev = self.array[3]
		dropout = self.array[4]
		s = self.get_truncated_normal(mean, stdev, min_val, max_val)
		s = s.rvs(8760)
		for i in range(len(s)):
			n = randint(0,100)
			dropout = math.floor(dropout)
			if (n < dropout):
				s[i] = 0
		return s

# Testing the distribution class.
test1 = distTruncRandNorm(PJM_primary)
s = test1.samplesAnnualHourly()

# Regulation Results
regulation_dist = [ERCOT_reg_up, ERCOT_reg_down, MISO_reg, NYSIO_E_reg, NYISO_W_reg, PJM_reg, SPP_UP_reg, SPP_DOWN_reg, CAISO_UP_reg, CAISO_DOWN_reg]
regulation_dist_name = ['ERCOT_reg_up', 'ERCOT_reg_down', 'MISO_reg', 'NYSIO_E_reg', 'NYISO_W_reg', 'PJM_reg', 'SPP_UP_reg', 'SPP_DOWN_reg', 'CAISO_UP_reg', 'CAISO_DOWN_reg']
d = {}

for i in range(len(regulation_dist)):
	dist = distTruncRandNorm(regulation_dist[i])
	s = dist.samplesAnnualHourly()
	d[regulation_dist_name[i]] = s
df_reg = pd.DataFrame(data=d)

df_reg.to_csv('res_regulation_prices.csv', index=False)

# Spinning Results
spinning_dist = [CAISO_EXP_spin, ERCOT_spin, MISO_spin, ISONE_spin, NYISO_W_spin, NYISO_E_spin, PJM_synch, SPP_spin]
spinning_dist_names = ['CAISO_EXP_spin', 'ERCOT_spin', 'MISO_spin', 'ISONE_spin', 'NYISO_W_spin', 'NYISO_E_spin', 'PJM_synch', 'SPP_spin']

d = {}
for i in range(len(spinning_dist)):
	dist = distTruncRandNorm(spinning_dist[i])
	s = dist.samplesAnnualHourly()
	d[spinning_dist_names[i]] = s
df_spin = pd.DataFrame(data=d)

df_spin.to_csv('res_spinning_prices.csv', index=False)

# No Spin Results
nospin_dist = [CAISO_EXP_nospin, ERCOT_nospin, MISO_supplemental, ISONE_nospin, ISONE_operating, NYISO_E_nospin, NYISO_W_nospin, NYISO_E_reserve30, NYISO_W_reserve30, PJM_primary, SPP_supplemental]
nospin_dist_names = ['CAISO_EXP_nospin', 'ERCOT_nospin', 'MISO_supplemental', 'ISONE_nospin', 'ISONE_operating', 'NYISO_E_nospin', 'NYISO_W_nospin', 'NYISO_E_reserve30', 'NYISO_W_reserve30', 'PJM_primary', 'SPP_supplemental']

d = {}
for i in range(len(nospin_dist)):
	dist = distTruncRandNorm(nospin_dist[i])
	s = dist.samplesAnnualHourly()
	d[nospin_dist_names[i]] = s
df_nospin = pd.DataFrame(data=d)

df_nospin.to_csv('res_non-spinning_prices.csv', index=False)
