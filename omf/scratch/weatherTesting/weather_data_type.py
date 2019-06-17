import re, datetime


def str_to_num(data):
	if type(data) is str or type(data) is unicode:
		if get_precision(data) == 0:
			return int(data)
		return float(data)
	return data


def get_precision(data):
	# type: (str) -> int
	if type(data) is not str and type(data) is not unicode:
		data = str(data)
	if data.find(".") == -1:
		return 0
	return len(re.split("[.]", data)[1])


def get_processed_row(data_types, row):
	# type: (list, list) -> list
	""" The order of the WeatherDataTypes in the data_types list determines the order of the data in the final processed csv row """
	processed_row = []
	for dt in data_types:
		processed_row.append(dt.get_value(row))
	return processed_row


def add_row_to_hourly_avg(row, hourly_avg):
	for j in range(len(row)):
		val = row[j]
		try:
			val = str_to_num(val)
			hourly_avg[j] += val
		except:
			hourly_avg[j] = val


def get_first_valid_row(rows, data_types, reverse=False):
	# type: (list, list, bool) -> list
	"""
	Iterate over rows and return the first row that has all valid data for the given WeatherDataTypes. If reversed is False, iterate from the earliest
	to the latest time in the year. If reversed is True, iterate from the latest to the earliest time in the year. Don't return a composite row
	because it's possible that a composite row would have values that don't make any sense together (e.g. 0 relative humidity and 12 inches of
	precipitation, each pulled from different datetimes and merged into a single row)
	"""
	if reverse:
		rows = reversed(rows)
	for row in rows:
		valid = True
		for dt in data_types:
			if not dt.validate(row):
				valid = False	
		if valid:
			return row


def extract_data(first_valid_row, last_valid_row, rows, data_types, is_subhourly_data=False):
	# type: (list, list, list, list, list, bool) -> list
	most_recent_valid_row = first_valid_row
	processed_data = []
	if is_subhourly_data:
		hourly_avg = [0] * len(rows[0])
	for i in range(len(rows)):
		row = rows[i]
		for dt in data_types:
			if not dt.validate(row):
				end_row_index, next_valid_value = dt.get_next_valid_value(rows, i)
				if end_row_index is None:
					end_row_index = len(rows) - 1
					next_valid_value = str_to_num(last_valid_row[dt.data_index])
				dt.correct_column(rows, i, end_row_index - 1, str_to_num(most_recent_valid_row[dt.data_index]), next_valid_value)
		most_recent_valid_row = row
		if is_subhourly_data:
			add_row_to_hourly_avg(row, hourly_avg)
			if (i + 1) % 12 == 0:
				for j in range(len(row)):
					try:
						hourly_avg[j] = hourly_avg[j] / float(12)
					except:
						pass
				processed_data.append(get_processed_row(data_types, hourly_avg))
				hourly_avg = [0] * len(row)
		else:
			processed_data.append(get_processed_row(data_types, row))
	return processed_data


def watts_per_meter_sq_to_watts_per_ft_sq(w_m_sq):
	# type: (int) -> float
	if type(w_m_sq) is str or type(w_m_sq) is unicode:
		w_m_sq = str_to_num(w_m_sq)
	return (w_m_sq / ((1 / .3048) ** 2))


def celsius_to_fahrenheit(c):
	if type(c) is str or type(c) is unicode:
		c = str_to_num(c)
	return c * 9 / float(5) + 32


def merge_hourly_subhourly(hourly, subhourly, insert_idx):
	# type: (list, list, int) -> list
	"""
	TODO: take a list of integers, where each integer specifies the ending index of some column. The number of integers must match the combined length
	of both lists.
	"""
	assert len(hourly) == 8760
	assert len(hourly) == len(subhourly)
	assert len(hourly[0]) > 0 and len(subhourly[0]) > 0
	merged_rows = []
	start_date = datetime.datetime(2000, 1, 1, 0, 0, 0) # arbitrary datetime, this could be any year
	hour = datetime.timedelta(hours=1)
	for i in range(len(hourly)):
		dt = start_date + hour * i
		gridlabd_date = '{}:{}:{}:{}:{}'.format(dt.month, dt.day, dt.hour, dt.minute, dt.second)
		row = [gridlabd_date]
		for j in range(len(hourly[i])):
			if insert_idx == j:
				row.extend(subhourly[i])
			row.append(hourly[i][j])			
		merged_rows.append(row)
	return merged_rows


class WeatherDataType(object):


	def __init__(self, data_index, missing_data_value, flag_index=None, transformation_function=None):
		# type: (int, int/float, int, function) -> None
		self.data_index = int(data_index)
		if type(missing_data_value) is str or type(missing_data_value) is unicode:
			missing_data_value = str_to_num(missing_data_value)
		self.missing_data_value = missing_data_value
		if flag_index is not None:
			flag_index = int(flag_index)
		self.flag_index = flag_index
		self.transformation_function = transformation_function


	def validate(self, row):
		# type: (list) -> bool
		""" Return True if the row has a valid data value for this WeatherDataType, otherwise False """
		if str_to_num(row[self.data_index]) == self.missing_data_value:
			return False
		if self.flag_index is not None and str_to_num(row[self.flag_index]) != 0:
			return False
		return True


	def get_next_valid_value(self, rows, start_row_idx):
		# type: (list, int) -> tuple
		""" Return the closest valid value in the column of the data for this DataType and the row index at which it was found. """
		for i in range(start_row_idx, len(rows)):
			row = rows[i]
			if self.validate(row):
				return (i, str_to_num(row[self.data_index]))
		return (None, None)


	def correct_column(self, rows, start_row_idx, end_row_idx, initial_val, final_val):
		# type: (list, int, int, float, float) -> None
		"""
		Modify the data to interpolate between the most recent valid value and the closest future valid value.
		- start_row_idx and end_row_idx are both inclusive of modification
		- need to maintain the same precision as the original measurement
		"""
		start_row_idx = int(start_row_idx)
		end_row_idx = int(end_row_idx)
		if type(initial_val) is str:
			initial_val = str_to_num(initial_val)
		if type(final_val) is str:
			final_val = str_to_num(final_val)
		precision = get_precision(initial_val)
		increment = (1.0 * final_val - initial_val) / (end_row_idx - start_row_idx + 2)
		count = 1
		for i in range(start_row_idx, end_row_idx + 1):
			row = rows[i]
			val = round((initial_val + increment * count), precision)
			if precision == 0:
				val = int(val)
			row[self.data_index] = val
			if self.flag_index is not None:
				row[self.flag_index] = 0
			count += 1


	def get_value(self, row):
		# type: (list) -> float
		value = row[self.data_index]
		if type(value) is str or type(value) is unicode:
			value = str_to_num(value)
		if self.transformation_function is not None:
			return self.transformation_function(value)
		return value