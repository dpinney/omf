import pandas as pd
from fbprophet import Prophet
from omf.loadForecast import suppress_stdout_stderr
from os.path import join as pJoin
import os

def train_prophet(df, modelDir, interval_width=0.99):
	# train and cache into modelDir
	m = Prophet(
		yearly_seasonality=True, daily_seasonality=True, interval_width=interval_width
	)
	m.add_country_holidays(country_name='US')
	with suppress_stdout_stderr():
		m.fit(df)

	# Predict the future.
	print "PREDICTING!"
	future = m.make_future_dataframe(periods=0)
	forecast = m.predict(future)
	# Merge in the historical data.
	forecast["y"] = [float(x) for x in df["y"]]
	forecast["outlier"] = [False for x in xrange(len(forecast))]
	# Backup the model.
	forecast.to_csv(pJoin(modelDir, "forecasted.csv"))
	return forecast

def detect_outliers(df, modelDir):
	# load cached df if exists, or call train_prophet
	try:
		forecast = pd.read_csv(pJoin(modelDir, "forecasted.csv"))
	except IOError:
		forecast = train_prophet(df, modelDir)
	# detect outliers
	for index, row in forecast.iterrows():
		yVal = float(row["y"])
		yHigh = float(row["yhat_upper"])
		yLow = float(row["yhat_lower"])
		if (yVal > yHigh) or (yVal < yLow):
			forecast.at[index, "outlier"] = True
	return forecast
