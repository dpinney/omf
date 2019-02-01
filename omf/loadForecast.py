"""
This contains the loadForecast algorithms

"""

import math
import numpy as np
import pandas as pd
from os.path import join as pJoin
from datetime import datetime as dt
from datetime import timedelta

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


def nextDayPeakKatrinaForecast(rawData, startDate, modelDir):
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
	time_model = svmNextDayPeakTime()
	size_model = SVR(C=10000, epsilon=0.25, gamma=0.0001)

	# get cross-validated time predictions over the full interval
	forecasted_peak_time = list(time_model._cv_predict(df=df).hour_pred)

	# convert these float hour values into ISO formatted dates and times
	dates = list(daily_dti.to_pydatetime())
	dates = dates[: len(forecasted_peak_time)]
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
	)

	return (forecasted_peak_time, forecasted_peak_demand)


def rollingZuccForecast(rawData, startDate):
	"""Forecasting with fbprophet"""
	from fbprophet import Prophet
	from fbprophet.diagnostics import cross_validation

	zucc = Prophet()
	dates = pd.date_range(start=startDate, periods=len(rawData), freq="H")
	input_df = pd.DataFrame(rawData, columns=["y", "temp"])
	input_df["ds"] = dates.to_pydatetime()
	zucc.fit(input_df)
	out_df = cross_validation(zucc, horizon="672 hours", period="672 hours")
	out_df.to_csv("~/zucca.csv")
	return (list(out_df.yhat), list(out_df.yhat_lower), list(out_df.yhat_upper))


class svmNextDayPeakTime:
	def __init__(self):
		from sklearn.svm import SVC, SVR

		self.classifier = SVC(C=10, gamma=0.001)
		self.morning_regressor = SVR(C=10, epsilon=0.05, gamma=0.1)
		self.afternoon_regressor = SVR(C=10, epsilon=0.25, gamma=0.1)

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
			hour_predictions_morning = self.morning_regressor.predict(x_morning)
			hour_predictions_afternoon = self.afternoon_regressor.predict(x_afternoon)

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
