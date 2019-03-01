"""
This contains the loadForecast algorithms

"""

import math, pulp
import numpy as np
import pandas as pd
import os
from os.path import join as pJoin
from datetime import datetime as dt
from datetime import timedelta, date
from sklearn.model_selection import GridSearchCV


class suppress_stdout_stderr(object):
	"""
	A context manager for doing a "deep suppression" of stdout and stderr in
	Python, i.e. will suppress all print, even if the print originates in a
	compiled C/Fortran sub-function.
	   This will not suppress raised exceptions, since exceptions are printed
	to stderr just before a script exits, and after the context manager has
	exited (at least, I think that is why it lets exceptions through).
	"""

	def __init__(self):
		# Open a pair of null files
		self.null_fds = [os.open(os.devnull, os.O_RDWR) for x in range(2)]
		# Save the actual stdout (1) and stderr (2) file descriptors.
		self.save_fds = (os.dup(1), os.dup(2))

	def __enter__(self):
		# Assign the null pointers to stdout and stderr.
		os.dup2(self.null_fds[0], 1)
		os.dup2(self.null_fds[1], 2)

	def __exit__(self, *_):
		# Re-assign the real stdout/stderr back to (1) and (2)
		os.dup2(self.save_fds[0], 1)
		os.dup2(self.save_fds[1], 2)
		# Close the null files
		os.close(self.null_fds[0])
		os.close(self.null_fds[1])


# source: https://www.energygps.com/HomeTools/PowerCalendar
nercHolidays = {
	dt(2019, 1, 1): "New Years",
	dt(2019, 5, 27): "Memorial",
	dt(2019, 7, 4): "Independence",
	dt(2019, 9, 2): "Labor",
	dt(2019, 11, 28): "Thanksgiving",
	dt(2019, 12, 25): "Christmas",
	dt(2020, 1, 1): "New Years",
	dt(2020, 5, 25): "Memorial",
	dt(2020, 7, 4): "Independence",
	dt(2020, 9, 7): "Labor",
	dt(2020, 11, 26): "Thanksgiving",
	dt(2020, 12, 25): "Christmas",
	dt(2021, 1, 1): "New Years",
	dt(2021, 5, 31): "Memorial",
	dt(2021, 7, 5): "Independence",
	dt(2021, 9, 6): "Labor",
	dt(2021, 11, 25): "Thanksgiving",
	dt(2021, 12, 25): "Christmas",
}

_default_params = {
	"peakSize": {"C": 10000, "epsilon": 0.25, "gamma": 0.0001},
	"peakTimeClassifier": {"C": 10, "gamma": 0.001},
	"peakTimeRegressorMorning": {"C": 10, "epsilon": 0.05, "gamma": 0.1},
	"peakTimeRegressorAfternoon": {"C": 10, "epsilon": 0.25, "gamma": 0.1},
}


def rollingDylanForecast(rawData, upBound, lowBound):
	"""
	This model takes the inputs rawData, a dataset that holds 8760 values in two columns with no indexes
	The first column rawData[:][0] holds the hourly demand for one year
	The second column rawData[:][1] holds the hourly temperature for one year
	upBound is the upper limit for forecasted data to not exceed as sometimes the forecasting is wonky
	lowBound is the lower limit for forecasted data to not exceed as sometimes the forecasting is wonky
	when values exceed upBound or go below lowBound they are set to None
	"""
	forecasted = []
	actual = []
	for w in range(len(rawData)):
		# need to start at 4 weeks+1 hour to get enough data to train so 4*7*24 = 672, the +1 is not necessary due to indexing starting at 0
		actual.append((rawData[w][0]))
		if w >= 672:
			x = np.array(
				[
					rawData[w - 168][1],
					rawData[w - 336][1],
					rawData[w - 504][1],
					rawData[w - 672][1],
				]
			)  # training temp
			y = np.array(
				[
					rawData[w - 168][0],
					rawData[w - 336][0],
					rawData[w - 504][0],
					rawData[w - 672][0],
				]
			)  # training demand
			z = np.polyfit(x, y, 1)
			p = np.poly1d(z)
			forecasted.append(float((p(rawData[w][1]))))
		else:
			forecasted.append(None)
	for i in range(len(forecasted)):
		if forecasted[i] > float(upBound):
			forecasted[i] = None
		elif forecasted[i] < float(lowBound):
			forecasted[i] = None
	MAE = 0  # Mean Average Error calculation
	for i in range(len(forecasted)):
		if forecasted[i] != None:
			MAE = MAE + abs(forecasted[i] - actual[i])
	MAE = math.trunc(MAE / len(forecasted))
	return (forecasted, MAE)
	"""
	forecasted is an 8760 list of demand values
	MAE is an int and is the mean average error of the forecasted/actual data correlation
	"""


def nextDayPeakKatrinaForecast(
	rawData, startDate, modelDir, params, returnActuals=False
):
	"""
	This model takes the inputs rawData, a dataset that holds hourly values in two columns with no indexes
	The first column rawData[:][0] holds the hourly demand
	The second column rawData[:][1] holds the hourly temperature
	modelDir is the directory the model is running in, for the purposes of having somewhere to write the df

	The model returns a tuple of two python lists. 
	The first list of the tuple contains ISO formatted datetime strings of the daily predicted peak times,
	the second list of the tuple contains floats of daily predicted peak demand.
	"""
	from sklearn.model_selection import cross_val_predict
	from sklearn.svm import SVR

	# loading rawData into pandas
	datetime_index = pd.date_range(start=startDate, periods=len(rawData), freq="H")
	input_df = pd.DataFrame(rawData, index=datetime_index)
	input_df.columns = ["demand", "tdy_temp"]
	input_df.to_csv(pJoin(modelDir, "indata.csv"))
	daily_dti = datetime_index.floor("D").unique()
	df = pd.DataFrame(index=daily_dti)

	# finessing the date
	df["tdy_weekend"] = (daily_dti.weekday == 5) | (daily_dti.weekday == 6)
	df["tmr_weekend"] = df.tdy_weekend.shift(-1)

	# finessing the temp
	tmp = input_df.tdy_temp.resample("D").mean()
	df["tdy_temp"] = tmp
	df["tmr_temp"] = tmp.shift(-1)

	# finessing the demand
	de = input_df.demand.resample("H").mean()
	peak_demand = de.resample("D").max()
	peak_time = de.resample("D").aggregate(
		lambda S: S.idxmax().hour + S.idxmax().minute / 60
	)
	# calculating two peaks per day: 0-12, 12-24
	peak_time_12 = de.resample("12H").aggregate(
		lambda S: S.idxmax().hour + S.idxmax().minute / 60
	)
	peak_time_m = peak_time_12[peak_time_12.index.hour == 0]
	peak_time_a = peak_time_12[peak_time_12.index.hour == 12].resample("D").sum()
	afternoon_peak_bool = peak_time >= 12

	df["tdy_peak_demand"] = peak_demand
	df["tmr_peak_demand"] = peak_demand.shift(-1)
	df["tmr_peak_time"] = peak_time.shift(-1)
	df["tmr_morning_peak"] = peak_time_m.shift(-1)
	df["tmr_afternoon_peak"] = peak_time_a.shift(-1)
	df["tmr_afternoon_peak_bool"] = afternoon_peak_bool.shift(-1)

	# cache it and dropNaN
	df = df.dropna()
	df.to_csv(pJoin(modelDir, "train_data.csv"))

	# initiate my model bois
	params, gridsearch = _cleanse_params(params)
	time_model = svmNextDayPeakTime()
	if not gridsearch:
		size_model = SVR(**params["peakSize"])
	else:
		size_model = GridSearchCV(SVR(), param_grid=params["peakSize"])

		# get cross-validated time predictions over the full interval
	forecasted_peak_time = list(time_model._cv_predict(df=df).hour_pred.shift(1))[
		1:
	]  # shift(1) shifts from tmr to tdy

	# convert these float hour values into ISO formatted dates and times
	dates = list(df.index.to_pydatetime())
	dates = dates[1:]
	for i in range(len(dates)):
		dates[i] += timedelta(hours=forecasted_peak_time[i])
	forecasted_peak_time = [date.isoformat() for date in dates]

	# get cross-validated demand predictions over the full interval
	forecasted_peak_demand = list(
		cross_val_predict(
			size_model,
			X=df[["tdy_peak_demand", "tdy_temp", "tmr_temp"]],
			y=df.tmr_peak_demand,
			cv=3,
		)
	)[
		1:
	]  # shifting from tmr to tdy

	if returnActuals:
		dates = list(df.index.to_pydatetime())
		dates = dates[: len(peak_time)]
		for i in range(len(dates)):
			dates[i] += timedelta(hours=peak_time[i])
		actual_peak_time = [date.isoformat() for date in dates]
		return (
			forecasted_peak_time,
			forecasted_peak_demand,
			actual_peak_time[1:],
			list(df.tdy_peak_demand)[1:],
		)
	else:
		return (forecasted_peak_time, forecasted_peak_demand)


def prophetForecast(rawData, startDate, modelDir, partitions):
	"""Forecasting with fbprophet"""
	from fbprophet import Prophet
	from fbprophet.diagnostics import cross_validation

	partitions = int(partitions)
	# initiate model
	prophet = Prophet()

	# put dates in df
	dates = pd.date_range(start=startDate, periods=len(rawData), freq="H")
	input_df = pd.DataFrame(rawData, columns=["y", "temp"])
	input_df["ds"] = dates.to_pydatetime()
	input_df.to_csv(pJoin(modelDir, "prophetin.csv"))

	# give prophet the input data
	with suppress_stdout_stderr():
		prophet.fit(input_df)

		# determine partition length for the cross-validation
	total_hours = len(input_df.ds)
	hp = total_hours // partitions  # horizon and period
	init = total_hours % partitions  # total_hours - hp * (partitions - 1)

	# train prophet w/ those partitions
	# take a moment to appreciate this stupid way to pass the durations
	out_df = cross_validation(
		prophet,
		initial="%d hours" % init,
		horizon="%d hours" % hp,
		period="%d hours" % hp,
	)
	out_df.to_csv(pJoin(modelDir, "prophetout.csv"))
	return (list(out_df.yhat), list(out_df.yhat_lower), list(out_df.yhat_upper))


def _cleanse_params(params):
	"""Fills in default values for a single model's params"""
	has_lists = False
	ret = _default_params.copy()
	for k, v in params.iteritems():
		if k == "peakTimeRegressor":
			# overwrite morning & afternoon
			for kwarg, kwvalue in v.iteritems():
				if type(kwvalue) is list:
					has_lists = True
				ret["peakTimeRegressorMorning"][kwarg] = kwvalue
				ret["peakTimeRegressorAfternoon"][kwarg] = kwvalue
		else:
			for kwarg, kwvalue in v.iteritems():
				if type(kwvalue) is list:
					has_lists = True
				ret[k][kwarg] = kwvalue

	if has_lists:
		for k, v in params.iteritems():
			for l, w in v.iteritems():
				if type(w) is not list:
					ret[k][l] = [w]

	return ret, has_lists


class svmNextDayPeakTime:
	def __init__(self, params=_default_params):
		from sklearn.svm import SVC, SVR

		params, gridSearch = _cleanse_params(params)
		if not gridSearch:
			self.classifier = SVC(**params["peakTimeClassifier"])
			self.morning_regressor = SVR(**params["peakTimeRegressorMorning"])
			self.afternoon_regressor = SVR(**params["peakTimeRegressorAfternoon"])
		else:
			self.classifier = GridSearchCV(
				SVC(), param_grid=params["peakTimeClassifier"]
			)
			self.morning_regressor = GridSearchCV(
				SVR(), param_grid=params["peakTimeRegressorMorning"]
			)
			self.afternoon_regressor = GridSearchCV(
				SVR(), param_grid=params["peakTimeRegressorAfternoon"]
			)

	def fit(self, csv):
		"""Fits using all of the given data in csv"""
		df = pd.read_csv(csv).dropna()
		x = df.loc[:, ["tmr_temp", "tmr_weekend"]]
		y = df.tmr_afternoon_peak_bool.astype("bool")

		# fit the models
		self.classifier.fit(x, y)
		self.morning_regressor.fit(x, df.tmr_morning_peak)
		self.afternoon_regressor.fit(x, df.tmr_afternoon_peak)

	def predict(self, csv):
		"""Predicts using all of the given data in csv.
		Returns the csv as a dataframe with an added hour_pred column."""
		df = pd.read_csv(csv, parse_dates=[0])
		x = df.loc[:, ["tmr_temp", "tmr_weekend"]]
		indices = []
		hour_pred = []
		for index, row in x.iterrows():
			classifier_prediction = self.classifier.predict([row])
			if classifier_prediction:
				hour_prediction = self.afternoon_regressor.predict([row])
			else:
				hour_prediction = self.morning_regressor.predict([row])
			indices.append(index)
			hour_pred.append(hour_prediction[0])
		hour_pred = pd.Series(data=hour_pred, index=indices)
		df["hour_pred"] = hour_pred
		return df

	def cv_metrics(self, csv, metric, random_state=None, splits=None, *args, **kwargs):
		"""Computes cross-validated metrics for the model."""
		# imports
		from sklearn.metrics import (
			explained_variance_score,
			mean_absolute_error,
			mean_squared_error,
			mean_squared_log_error,
			median_absolute_error,
			r2_score,
		)

		# dicty boi for passing in metrics as strings
		metric_string_to_function = {
			"explained_variance_score": explained_variance_score,
			"mean_absolute_error": mean_absolute_error,
			"mean_squared_error": mean_squared_error,
			"mean_squared_log_error": mean_squared_log_error,
			"median_absolute_error": median_absolute_error,
			"r2_score": r2_score,
		}
		if metric not in metric_string_to_function.keys():
			print "Metric not recognized"
			return np.nan
		df = pd.read_csv(csv).dropna()
		y = df.tmr_peak_time
		metric = metric_string_to_function.get(metric, np.nan)
		results = self._cv_predict(
			csv, random_state=random_state, splits=splits if splits else 3
		)
		return metric(y, results, **kwargs)

	def _cv_predict(
		self, csv=None, df=None, random_state=None, splits=3
	):  # cross-validated predict
		"""Returns cross validated prediction as column of pandas dataframe"""
		from sklearn.model_selection import StratifiedKFold

		self._cv_classifiers = []
		self._cv_morning_regressors = []
		self._cv_afternoon_regressors = []
		self.skf = StratifiedKFold(
			shuffle=True, random_state=random_state, n_splits=splits
		)

		if csv and not df:
			df = (
				pd.read_csv(csv, parse_dates=[0])
				.dropna()
				.rename(columns={"Unnamed: 0": "Time"})
			)
			df = df.resample("D", on="Time").max()
		ks = df.loc[
			:, ["tmr_temp", "tmr_weekend", "tmr_morning_peak", "tmr_afternoon_peak"]
		]
		y = df.tmr_afternoon_peak_bool.astype("bool")

		hourpred = pd.Series(index=df.index)
		# loop over the splits, training and predicting appropiately
		for train_index, test_index in self.skf.split(ks, y):
			ks_train, ks_test, y_train, y_test = (
				ks.iloc[train_index, :],
				ks.iloc[test_index, :],
				y.iloc[train_index],
				y.iloc[test_index],
			)
			x_train, x_test = (
				ks_train.loc[:, ["tmr_temp", "tmr_weekend"]],
				ks_test.loc[:, ["tmr_temp", "tmr_weekend"]],
			)

			###FITTING ON TRAINING DATA
			self.classifier.fit(x_train, y_train)
			self.morning_regressor.fit(x_train, ks_train.tmr_morning_peak)
			self.afternoon_regressor.fit(x_train, ks_train.tmr_afternoon_peak)

			###PREDICTING ON TESTING DATA
			classifier_predictions = self.classifier.predict(
				x_test
			)  # returns True if afternoon
			x_morning = x_test[~classifier_predictions]
			x_afternoon = x_test[classifier_predictions]

			hour_predictions_morning = (
				self.morning_regressor.predict(x_morning)
				if len(x_morning) > 0
				else np.array([])
			)
			hour_predictions_afternoon = (
				self.afternoon_regressor.predict(x_afternoon)
				if len(x_afternoon) > 0
				else np.array([])
			)

			###APPENDING RESULTS & SKLEARN OBJECTS
			for hpm_index, index_val in enumerate(
				df.index[test_index][~classifier_predictions]
			):
				hourpred[index_val] = hour_predictions_morning[hpm_index]
			for hpm_index, index_val in enumerate(
				df.index[test_index][classifier_predictions]
			):
				hourpred[index_val] = hour_predictions_afternoon[hpm_index]

			self._cv_classifiers.append(self.classifier)
			self._cv_morning_regressors.append(self.morning_regressor)
			self._cv_afternoon_regressors.append(self.afternoon_regressor)
		df["hour_pred"] = hourpred
		return df


# NERC6 holidays with inconsistent dates. Created with python holidays package
# years 1990 - 2024
nerc6 = {
	"Memorial Day": [
		date(1990, 5, 28),
		date(1991, 5, 27),
		date(1992, 5, 25),
		date(1993, 5, 31),
		date(1994, 5, 30),
		date(1995, 5, 29),
		date(1996, 5, 27),
		date(1997, 5, 26),
		date(1998, 5, 25),
		date(1999, 5, 31),
		date(2000, 5, 29),
		date(2001, 5, 28),
		date(2002, 5, 27),
		date(2003, 5, 26),
		date(2004, 5, 31),
		date(2005, 5, 30),
		date(2006, 5, 29),
		date(2007, 5, 28),
		date(2008, 5, 26),
		date(2009, 5, 25),
		date(2010, 5, 31),
		date(2011, 5, 30),
		date(2012, 5, 28),
		date(2013, 5, 27),
		date(2014, 5, 26),
		date(2015, 5, 25),
		date(2016, 5, 30),
		date(2017, 5, 29),
		date(2018, 5, 28),
		date(2019, 5, 27),
		date(2020, 5, 25),
		date(2021, 5, 31),
		date(2022, 5, 30),
		date(2023, 5, 29),
		date(2024, 5, 27),
	],
	"Labor Day": [
		date(1990, 9, 3),
		date(1991, 9, 2),
		date(1992, 9, 7),
		date(1993, 9, 6),
		date(1994, 9, 5),
		date(1995, 9, 4),
		date(1996, 9, 2),
		date(1997, 9, 1),
		date(1998, 9, 7),
		date(1999, 9, 6),
		date(2000, 9, 4),
		date(2001, 9, 3),
		date(2002, 9, 2),
		date(2003, 9, 1),
		date(2004, 9, 6),
		date(2005, 9, 5),
		date(2006, 9, 4),
		date(2007, 9, 3),
		date(2008, 9, 1),
		date(2009, 9, 7),
		date(2010, 9, 6),
		date(2011, 9, 5),
		date(2012, 9, 3),
		date(2013, 9, 2),
		date(2014, 9, 1),
		date(2015, 9, 7),
		date(2016, 9, 5),
		date(2017, 9, 4),
		date(2018, 9, 3),
		date(2019, 9, 2),
		date(2020, 9, 7),
		date(2021, 9, 6),
		date(2022, 9, 5),
		date(2023, 9, 4),
		date(2024, 9, 2),
	],
	"Thanksgiving": [
		date(1990, 11, 22),
		date(1991, 11, 28),
		date(1992, 11, 26),
		date(1993, 11, 25),
		date(1994, 11, 24),
		date(1995, 11, 23),
		date(1996, 11, 28),
		date(1997, 11, 27),
		date(1998, 11, 26),
		date(1999, 11, 25),
		date(2000, 11, 23),
		date(2001, 11, 22),
		date(2002, 11, 28),
		date(2003, 11, 27),
		date(2004, 11, 25),
		date(2005, 11, 24),
		date(2006, 11, 23),
		date(2007, 11, 22),
		date(2008, 11, 27),
		date(2009, 11, 26),
		date(2010, 11, 25),
		date(2011, 11, 24),
		date(2012, 11, 22),
		date(2013, 11, 28),
		date(2014, 11, 27),
		date(2015, 11, 26),
		date(2016, 11, 24),
		date(2017, 11, 23),
		date(2018, 11, 22),
		date(2019, 11, 28),
		date(2020, 11, 26),
		date(2021, 11, 25),
		date(2022, 11, 24),
		date(2023, 11, 23),
		date(2024, 11, 28),
	],
	"Independence Day (Observed)": [
		date(1992, 7, 3),
		date(1993, 7, 5),
		date(1998, 7, 3),
		date(1999, 7, 5),
		date(2004, 7, 5),
		date(2009, 7, 3),
		date(2010, 7, 5),
		date(2015, 7, 3),
		date(2020, 7, 3),
		date(2021, 7, 5),
	],
	"New Year's Day (Observed)": [
		date(1993, 12, 31),
		date(1995, 1, 2),
		date(1999, 12, 31),
		date(2004, 12, 31),
		date(2006, 1, 2),
		date(2010, 12, 31),
		date(2012, 1, 2),
		date(2017, 1, 2),
		date(2021, 12, 31),
		date(2023, 1, 2),
	],
	"Christmas Day (Observed)": [
		date(1993, 12, 24),
		date(1994, 12, 26),
		date(1999, 12, 24),
		date(2004, 12, 24),
		date(2005, 12, 26),
		date(2010, 12, 24),
		date(2011, 12, 26),
		date(2016, 12, 26),
		date(2021, 12, 24),
		date(2022, 12, 26),
	],
}


def isHoliday(holiday, df):
	# New years, memorial, independence, labor day, Thanksgiving, Christmas
	m1 = None
	if holiday == "New Year's Day":
		m1 = (df["dates"].dt.month == 1) & (df["dates"].dt.day == 1)
	if holiday == "Independence Day":
		m1 = (df["dates"].dt.month == 7) & (df["dates"].dt.day == 4)
	if holiday == "Christmas Day":
		m1 = (df["dates"].dt.month == 12) & (df["dates"].dt.day == 25)
	m1 = df["dates"].dt.date.isin(nerc6[holiday]) if m1 is None else m1
	m2 = df["dates"].dt.date.isin(nerc6.get(holiday + " (Observed)", []))
	return m1 | m2


def makeUsefulDf(df):
	"""
	Turn a dataframe of datetime and load data into a dataframe useful for
	machine learning. Normalize values and turn 
	Features are placed into r_df (return dataframe), creates the following columns

		YEARS SINCE 2000

		LOAD AT THIS TIME DAY BEFORE

		HOUR OF DAY
		- is12AM (0, 1)
		- is1AM (0, 1)
		...
		- is11PM (0, 1)

		DAYS OF THE WEEK
		- isSunday (0, 1)
		- isMonday (0, 1)
		...
		- isSaturday (0, 1)

		MONTHS OF THE YEAR
		- isJanuary (0, 1)
		- isFebruary (0, 1)
		...
		- isDecember (0, 1)

		TEMPERATURE
		- Celcius (normalized from -1 to 1)

		PREVIOUS DAY'S LOAD 
		- 12AM of day previous (normalized from -1 to 1)
		- 1AM of day previous (normalized from -1 to 1)
		...
		- 11PM of day previous (normalized from -1 to 1)

		HOLIDAYS (the nerc6 holidays)
		- isNewYears (0, 1)
		- isMemorialDay (0, 1)
		...
		- is Christmas (0, 1)

	"""

	def _normalizeCol(l):
		s = l.max() - l.min()
		return l if s == 0 else (l - l.mean()) / s

	def _chunks(l, n):
		return [l[i : i + n] for i in range(0, len(l), n)]

	r_df = pd.DataFrame()
	r_df["load_n"] = _normalizeCol(df["load"])
	r_df["years_n"] = _normalizeCol(df["dates"].dt.year - 2000)

	# fix outliers
	m = df["tempc"].replace([-9999], np.nan)
	m.ffill(inplace=True)
	r_df["temp_n"] = _normalizeCol(m)

	# add the value of the load 24hrs before
	r_df["load_prev_n"] = r_df["load_n"].shift(24)
	r_df["load_prev_n"].bfill(inplace=True)

	# create day of week vector
	r_df["day"] = df["dates"].dt.dayofweek  # 0 is Monday.
	w = ["S", "M", "T", "W", "R", "F", "A"]
	for i, d in enumerate(w):
		r_df[d] = (r_df["day"] == i).astype(int)

		# create hour of day vector
	r_df["hour"] = df["dates"].dt.hour
	d = [("h" + str(i)) for i in range(24)]
	for i, h in enumerate(d):
		r_df[h] = (r_df["hour"] == i).astype(int)

		# create month vector
	r_df["month"] = df["dates"].dt.month
	y = [("m" + str(i)) for i in range(12)]
	for i, m in enumerate(y):
		r_df[m] = (r_df["month"] == i).astype(int)

		# create 'load day before' vector
	n = np.array([val for val in _chunks(list(r_df["load_n"]), 24) for _ in range(24)])
	l = ["l" + str(i) for i in range(24)]
	for i, s in enumerate(l):
		r_df[s] = n[:, i]

		# create holiday booleans
	r_df["isNewYears"] = isHoliday("New Year's Day", df)
	r_df["isMemorialDay"] = isHoliday("Memorial Day", df)
	r_df["isIndependenceDay"] = isHoliday("Independence Day", df)
	r_df["isLaborDay"] = isHoliday("Labor Day", df)
	r_df["isThanksgiving"] = isHoliday("Thanksgiving", df)
	r_df["isChristmas"] = isHoliday("Christmas Day", df)

	m = r_df.drop(["month", "hour", "day", "load_n"], axis=1)
	return m


def shouldDispatchPS(peak, month, df, conf):
	"""
	Heuristic to determine whether or not a day's peak is worth dispatching 
	when the goal is to shave monthly peaks.
	"""
	return peak > df[:-8760].groupby("month")["load"].quantile(conf)[month]


def shouldDispatchDeferral(peak, df, conf, threshold):
	"""
	Heuristic to determine whether or not a day's peak is worth dispatching 
	when the goal is not to surpass a given threshold.
	"""
	return peak > threshold * conf


def pulp24hrVbat(ind, demand, P_lower, P_upper, E_UL):
	"""
	Given input dictionary, the limits on the battery, and the demand curve, 
	minimize the peaks for a day.
	"""
	alpha = 1 - (
		1 / (float(ind["capacitance"]) * float(ind["resistance"]))
	)  # 1-(deltaT/(C*R)) hourly self discharge rate
	# LP Variables
	model = pulp.LpProblem("Daily demand charge minimization problem", pulp.LpMinimize)
	VBpower = pulp.LpVariable.dicts(
		"ChargingPower", range(24)
	)  # decision variable of VB charging power; dim: 8760 by 1
	VBenergy = pulp.LpVariable.dicts(
		"EnergyState", range(24)
	)  # decision variable of VB energy state; dim: 8760 by 1

	for i in range(24):
		VBpower[i].lowBound = -1 * P_lower[i]
		VBpower[i].upBound = P_upper[i]
		VBenergy[i].lowBound = -1 * E_UL[i]
		VBenergy[i].upBound = E_UL[i]
	pDemand = pulp.LpVariable("Peak Demand", lowBound=0)

	# Objective function: Minimize peak demand
	model += pDemand

	# VB energy state as a function of VB power
	model += VBenergy[0] == VBpower[0]
	for i in range(1, 24):
		model += VBenergy[i] == alpha * VBenergy[i - 1] + VBpower[i]
	for i in range(24):
		model += pDemand >= demand[i] + VBpower[i]
	model.solve()
	return (
		[VBpower[i].varValue for i in range(24)],
		[VBenergy[i].varValue for i in range(24)],
	)


def pulp24hrBattery(demand, power, energy, battEff):
	# LP Variables
	model = pulp.LpProblem("Daily demand charge minimization problem", pulp.LpMinimize)
	VBpower = pulp.LpVariable.dicts(
		"ChargingPower", range(24)
	)  # decision variable of VB charging power; dim: 24 by 1
	VBenergy = pulp.LpVariable.dicts(
		"EnergyState", range(24)
	)  # decision variable of VB energy state; dim: 24 by 1

	for i in range(24):
		VBpower[i].lowBound = -power
		VBpower[i].upBound = power
		VBenergy[i].lowBound = 0
		VBenergy[i].upBound = energy
	pDemand = pulp.LpVariable("Peak Demand", lowBound=0)

	# Objective function: Minimize peak demand
	model += pDemand

	# VB energy state as a function of VB power
	model += VBenergy[0] == 0
	for i in range(1, 24):
		model += VBenergy[i] == battEff * VBenergy[i - 1] + VBpower[i]
	for i in range(24):
		model += pDemand >= demand[i] + VBpower[i]
	model.solve()
	return (
		[VBpower[i].varValue for i in range(24)],
		[VBenergy[i].varValue for i in range(24)],
	)


def neural_net_predictions(all_X, all_y):
	import tensorflow as tf
	from tensorflow.keras import layers

	X_train, y_train = all_X[:-8760], all_y[:-8760]

	model = tf.keras.Sequential(
		[
			layers.Dense(
				all_X.shape[1], activation=tf.nn.relu, input_shape=[len(X_train.keys())]
			),
			layers.Dense(all_X.shape[1], activation=tf.nn.relu),
			layers.Dense(all_X.shape[1], activation=tf.nn.relu),
			layers.Dense(1),
		]
	)

	optimizer = tf.keras.optimizers.RMSprop(0.001)

	model.compile(
		loss="mean_squared_error",
		optimizer=optimizer,
		metrics=["mean_absolute_error", "mean_squared_error"],
	)

	EPOCHS = 10

	early_stop = tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=10)

	history = model.fit(
		X_train,
		y_train,
		epochs=EPOCHS,
		validation_split=0.2,
		verbose=0,
		callbacks=[early_stop],
	)

	return [float(f) for f in model.predict(all_X[-8760:])]
