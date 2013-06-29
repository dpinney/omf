'''Process user-inputted SCADA data.

Currently, this is just a place holder for a function that will take the name of the SCADA file and return the necessary measurement points for use in the calibration function.

'''

def getValues(input):

	# From the SCADA available, choose three days representing summer, winter, and spring (shoulder).
	# Ideally, summer and winter days are seasonal peak days.
	# summer_day = '2012-06-29'
	# winter_day = '2012-01-04'
	# shoulder_day = '2012-04-14'
	summer_day = '2012-06-29'
	winter_day = '2012-01-19'
	shoulder_day = '2012-04-10'
	
	# for four-node test:
	# summer day measurements
	# su_peak_value = 2250  # kW
	# su_total_energy = 38746.05433 # kWh
	# su_peak_time = 17.92  # hour
	# su_minimum_value = 993.8051117  # kW
	# su_minimum_time = 3.92  # hour
	# # winter day measurements
	# wi_peak_value = 1200  # kW
	# wi_total_energy = 23476.8931  # kWh
	# wi_peak_time = 7.25  # hour
	# wi_minimum_value = 794.967232  # kW
	# wi_minimum_time = 22.50  # hour
	# # spring day measurements
	# sh_peak_value = 1146  # kW
	# sh_total_energy = 23172.99087  #kWh
	# sh_peak_time = 20.67  # hour
	# sh_minimum_value = 749.0278833  # kW
	# sh_minimum_time = 1.58  # hour
	
	# for FRIENDSHIP 2012:
	# summer day measurements
	su_peak_value = 5931.36  # kW
	su_total_energy = 107380.8 # kWh
	su_peak_time = 17  # hour
	su_minimum_value = 2988  # kW
	su_minimum_time = 6  # hour
	# winter day measurements
	wi_peak_value = 3646.08  # kW
	wi_total_energy = 75604.32  # kWh
	wi_peak_time = 21  # hour
	wi_minimum_value = 2469.60  # kW
	wi_minimum_time = 1  # hour
	# spring day measurements
	sh_peak_value = 2518.56  # kW
	sh_total_energy = 52316.64  #kWh
	sh_peak_time = 21  # hour
	sh_minimum_value = 1738.08  # kW
	sh_minimum_time = 2  # hour
	
	# It is important that values are returned in the correct order.
	return [summer_day, winter_day, shoulder_day], [ [su_peak_value, su_peak_time, su_total_energy, su_minimum_value, su_minimum_time],[wi_peak_value, wi_peak_time, wi_total_energy, wi_minimum_value, wi_minimum_time], [sh_peak_value, sh_peak_time, sh_total_energy, sh_minimum_value, sh_minimum_time] ]
	
def main():
	days, SCADA = getValues(None);
	print (__doc__)
	print ("Three chosen days are "+str(days))
	print ("Peak Value (kw), Peak Time (hour), Total Energy (kwh), Minimum Value (kw), Minimum Time (hour) for: ")
	print ("Summer " +str(SCADA[0]))
	print ("Winter " +str(SCADA[1]))
	print ("Shoulder " +str(SCADA[2]))

if __name__ ==  '__main__':
	main();