import os
import pandas as pd

mega_df = []
for file_name in os.listdir("./xlsx"):
	tmp = pd.read_excel(os.path.join("./xlsx", file_name)).rename(
		{
			"HourEnding": "HOUR",
			"Hour Ending": "HOUR",
			"Hour_End": "HOUR",
			"SOUTH_C": "SCENT",
			"NORTH_C": "NCENT",
			"FAR_WEST": "FWEST",
			"SOUTHERN": "SOUTH",
		},
		axis=1,
	)
	mega_df.append(tmp)

kw = pd.concat(mega_df)
indices_to_delete = []
years = dict()
for i, row in kw.iterrows():
	dt = row['HOUR']
	year = str(dt)[:5]
	if year in years:
		years[year] += 1
	else:
		years[year] = 1
	if years[year] > 8760:
		indices_to_delete.append(i)

kw.drop(indices_to_delete)
	
we = pd.DataFrame()
for file_name in os.listdir("./weather"):
	tmp = pd.read_csv(os.path.join("./weather", file_name))
	# concat the columns into a mega column
	tmp = pd.concat([tmp[s] for s in tmp.columns]).reset_index(drop=True)
	we[file_name.split(".")[0]] = tmp
	# and then add that to the mega_df as LOC_weather

kw.columns = [a + "_KW" for a in kw.columns]
we.columns = [a + "_TEMP" for a in we.columns]

for col in we.columns:
	kw[col] = we[col]

for a in ["COAST", "EAST", "FWEST", "NORTH", "NCENT", "SCENT", "SOUTH", "WEST"]:
	sub = kw[[a + "_KW", a + "_TEMP"]]
	sub.to_csv(a + ".csv", header=False, index=False)
