"""
This contains the loadForecast algorithms

"""

import math, pulp
import numpy as np
import pandas as pd
from os.path import join as pJoin
from datetime import datetime as dt
from datetime import timedelta, date
from sklearn.model_selection import GridSearchCV

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
