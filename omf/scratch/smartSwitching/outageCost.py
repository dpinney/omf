import pandas as pd

def manualOutageStats(numberOfCustomers, pathToCSV, sustainedOutageThreshold):
	'function which computes outage stats given the number of total customers, an input csv file, and threshold for a sustained outage'
	mc = pd.read_csv(pathToCSV)

	# calculate SAIDI
	customerInterruptionDurations = 0.0
	row = 0
	row_count_mc = mc.shape[0]
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
			customerInterruptionDurations += (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) * len(mc.loc[row, 'Meters Affected']) / 3600
		row += 1

	SAIDI = customerInterruptionDurations / numberOfCustomers

	# calculate SAIFI
	row = 0
	totalInterruptions = 0.0
	customersAffected = 0
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) > int(sustainedOutageThreshold):
			customersAffected += len(mc.loc[row, 'Meters Affected'])
		row += 1
	SAIFI = customersAffected / numberOfCustomers

	# calculate CAIDI
	CAIDI = SAIDI / SAIFI

	# calculate ASAI
	ASAI = (numberOfCustomers * 8760 - customerInterruptionDurations) / (numberOfCustomers * 8760)

	# calculate MAIFI
	sumCustomersAffected = 0.0
	row = 0
	while row < row_count_mc:
		if (datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Finish'], '%Y-%m-%d %H:%M:%S')) - datetime_to_float(datetime.datetime.strptime(mc.loc[row, 'Start'], '%Y-%m-%d %H:%M:%S'))) <= int(sustainedOutageThreshold):
			sumCustomersAffected += len(mc.loc[row, 'Meters Affected'])
		row += 1

	MAIFI = sumCustomersAffected / numberOfCustomers

	# return values
	return SAIDI, SAIFI, CAIDI, ASAI, MAIFI