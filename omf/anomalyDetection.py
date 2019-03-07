import pandas as pd
try:
	from fbprophet import Prophet
except:
	pass # fbprophet is very badly behaved at runtime and also at install time.
from omf.loadForecast import suppress_stdout_stderr
from os.path import join as pJoin
import os


def train_prophet(df, modelDir, confidence=0.99):
	# train and cache into modelDir
	m = Prophet(
		yearly_seasonality=True, daily_seasonality=True, interval_width=confidence
	)
	with suppress_stdout_stderr():
		m.fit(df)

		# Predict the future.
	print "PREDICTING!"
	future = m.make_future_dataframe(periods=0)
	forecast = m.predict(future)
	# Merge in the historical data.
	forecast["y"] = df.y.astype(float)
	# Backup the model.
	forecast.to_csv(
		pJoin(modelDir, "forecasted_{}.csv".format(confidence)), index=False
	)
	return forecast


def prophet(df, modelDir, confidence=0.99, cached=""):
	# load cached df if exists, or call train_prophet
	if cached and os.path.isfile(pJoin(modelDir, cached)):
		forecast = pd.read_csv(pJoin(modelDir, cached))
	else:
		forecast = train_prophet(df, modelDir, confidence)
		# detect outliers
	cols = ["y", "yhat", "yhat_lower", "yhat_upper"]
	forecast[cols] = forecast[cols].astype(float)
	forecast["outlier"] = (forecast.y > forecast.yhat_upper) | (
		forecast.y < forecast.yhat_lower
	)
	return forecast


def elliptic_envelope(df, modelDir, norm_confidence=0.95):
	from sklearn.covariance import EllipticEnvelope
	from scipy.stats import normaltest

	if "ds" in df.columns:
		del df["ds"]
	model = EllipticEnvelope()
	test_stats, p_vals = normaltest(df.values, axis=0)
	normal_cols = p_vals >= (1 - norm_confidence)
	df = df.loc[:, normal_cols]
	if df.shape[1] == 0:
		return None
	df.outlier = model.fit_predict(df.values)
	df.outlier = df.outlier < 0  # 1 if inlier, -1 if outlier
	return df
