import gridlabd_weather_validation as aGosedWeather
from gridlabd_weather_validation import USCRNDataType
import requests
import csv, os


"""
This script has some functions for assessing how much data for a given year and station is invalid. We currently are not interested in this
functionality however.
"""


# There are 156 stations
stations = [
	"AK_Bethel_87_WNW",
	"AK_Cordova_14_ESE",
	"AK_Deadhorse_3_S",
	"AK_Denali_27_N",
	"AK_Fairbanks_11_NE",
	"AK_Glennallen_64_N",
	"AK_Gustavus_2_NE",
	"AK_Ivotuk_1_NNE",
	"AK_Kenai_29_ENE",
	"AK_King_Salmon_42_SE",
	"AK_Metlakatla_6_S",
	"AK_Port_Alsworth_1_SW",
	"AK_Red_Dog_Mine_3_SSW",
	"AK_Ruby_44_ESE",
	"AK_Sand_Point_1_ENE",
	"AK_Selawik_28_E",
	"AK_Sitka_1_NE",
	"AK_St._Paul_4_NE",
	"AK_Tok_70_SE",
	"AK_Toolik_Lake_5_ENE",
	"AK_Utqiagvik_formerly_Barrow_4_ENE",
	"AK_Yakutat_3_SSE",
	"AL_Brewton_3_NNE",
	"AL_Clanton_2_NE",
	"AL_Courtland_2_WSW",
	"AL_Cullman_3_ENE",
	"AL_Fairhope_3_NE",
	"AL_Gadsden_19_N",
	"AL_Gainesville_2_NE",
	"AL_Greensboro_2_WNW",
	"AL_Highland_Home_2_S",
	"AL_Muscle_Shoals_2_N",
	"AL_Northport_2_S",
	"AL_Russellville_4_SSE",
	"AL_Scottsboro_2_NE",
	"AL_Selma_6_SSE",
	"AL_Selma_13_WNW",
	"AL_Talladega_10_NNE",
	"AL_Thomasville_2_S",
	"AL_Troy_2_W",
	"AL_Valley_Head_1_SSW",
	"AR_Batesville_8_WNW",
	"AZ_Elgin_5_S",
	"AZ_Tucson_11_W",
	"AZ_Williams_35_NNW",
	"AZ_Yuma_27_ENE",
	"CA_Bodega_6_WSW",
	"CA_Fallbrook_5_NE",
	"CA_Merced_23_WSW",
	"CA_Redding_12_WNW",
	"CA_Santa_Barbara_11_W",
	"CA_Stovepipe_Wells_1_SW",
	"CA_Yosemite_Village_12_W",
	"CO_Boulder_14_W",
	"CO_Cortez_8_SE",
	"CO_Dinosaur_2_E",
	"CO_La_Junta_17_WSW",
	"CO_Montrose_11_ENE",
	"CO_Nunn_7_NNE",
	"FL_Everglades_City_5_NE",
	"FL_Sebring_23_SSE",
	"FL_Titusville_7_E",
	"GA_Brunswick_23_S",
	"GA_Newton_8_W",
	"GA_Newton_11_SW",
	"GA_Watkinsville_5_SSE",
	"HI_Hilo_5_S",
	"HI_Mauna_Loa_5_NNE",
	"IA_Des_Moines_17_E",
	"ID_Arco_17_SW",
	"ID_Murphy_10_W",
	"IL_Champaign_9_SW",
	"IL_Shabbona_5_NNE",
	"IN_Bedford_5_WNW",
	"KS_Manhattan_6_SSW",
	"KS_Oakley_19_SSW",
	"KY_Bowling_Green_21_NNE",
	"KY_Versailles_3_NNW",
	"LA_Lafayette_13_SE",
	"LA_Monroe_26_N",
	"ME_Limestone_4_NNW",
	"ME_Old_Town_2_W",
	"MI_Chatham_1_SE",
	"MI_Gaylord_9_SSW",
	"MN_Goodridge_12_NNW",
	"MN_Sandstone_6_W",
	"MO_Chillicothe_22_ENE",
	"MO_Joplin_24_N",
	"MO_Salem_10_W",
	"MS_Holly_Springs_4_N",
	"MS_Newton_5_ENE",
	"MT_Dillon_18_WSW",
	"MT_Lewistown_42_WSW",
	"MT_St._Mary_1_SSW",
	"MT_Wolf_Point_29_ENE",
	"MT_Wolf_Point_34_NE",
	"NC_Asheville_8_SSW",
	"NC_Asheville_13_S",
	"NC_Durham_11_W",
	"ND_Jamestown_38_WSW",
	"ND_Medora_7_E",
	"ND_Northgate_5_ESE",
	"NE_Harrison_20_SSE",
	"NE_Lincoln_8_ENE",
	"NE_Lincoln_11_SW",
	"NE_Whitman_5_ENE",
	"NH_Durham_2_N",
	"NH_Durham_2_SSW",
	"NM_Las_Cruces_20_N",
	"NM_Los_Alamos_13_W",
	"NM_Socorro_20_N",
	"NV_Baker_5_W",
	"NV_Denio_52_WSW",
	"NV_Mercury_3_SSW",
	"NY_Ithaca_13_E",
	"NY_Millbrook_3_W",
	"OH_Wooster_3_SSE",
	"OK_Goodwell_2_E",
	"OK_Goodwell_2_SE",
	"OK_Stillwater_2_W",
	"OK_Stillwater_5_WNW",
	"ON_Egbert_1_W",
	"OR_Coos_Bay_8_SW",
	"OR_Corvallis_10_SSW",
	"OR_John_Day_35_WNW",
	"OR_Riley_10_WSW",
	"PA_Avondale_2_N",
	"RI_Kingston_1_NW",
	"RI_Kingston_1_W",
	"SC_Blackville_3_W",
	"SC_McClellanville_7_NE",
	"SD_Aberdeen_35_WNW",
	"SD_Buffalo_13_ESE",
	"SD_Pierre_24_S",
	"SD_Sioux_Falls_14_NNE",
	"TN_Crossville_7_NW",
	"TX_Austin_33_NW",
	"TX_Bronte_11_NNE",
	"TX_Edinburg_17_NNE",
	"TX_Monahans_6_ENE",
	"TX_Muleshoe_19_S",
	"TX_Palestine_6_WNW",
	"TX_Panther_Junction_2_N",
	"TX_Port_Aransas_32_NNE",
	"UT_Brigham_City_28_WNW",
	"UT_Torrey_7_E",
	"VA_Cape_Charles_5_ENE",
	"VA_Charlottesville_2_SSE",
	"WA_Darrington_21_NNE",
	"WA_Quinault_4_NE",
	"WA_Spokane_17_SSW",
	"WI_Necedah_5_WNW",
	"WV_Elkins_21_ENE",
	"WY_Lander_11_SSE",
	"WY_Moose_1_NNE",
	"WY_Sundance_8_NNW"
]


def write_uscrn_metadata(year, stations, frequency, csv_path, filter_data=False):
	# type: (int, list, str, bool) -> dict
	"""
	{
		<station>: ["hourly", 2018, "AK_...", 8760, 8750, 10]
	}
	"""
	year = int(year)
	assert type(frequency) is str
	with open(csv_path, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(["Frequency", "Year", "Station Name", "Total Lines", "Valid Lines", "Invalid Lines"])
	if frequency == "hourly":
		temperature = USCRNDataType(8, -9999.0) 
		humidity = USCRNDataType(26, -9999, 27)
		solar_global = USCRNDataType(13, -99999, 14)
		data_types = [temperature, humidity, solar_global]
	if frequency == "subhourly":
		wind_speed = USCRNDataType(21, -99.00, 22)
		data_types = [wind_speed]
	for s in stations:
		rows = aGosedWeather.get_USCRN_data(year, s, frequency)
		if rows is None:
			continue
		line_count = len(rows)
		if filter_data:
			if frequency == "hourly":
				if line_count != 8760:
					continue
			if frequency == "subhourly":
				if line_count != 105120:
					continue
		valid_lines = 0
		invalid_lines = 0
		for row in rows:
			valid = True
			for dt in data_types:
				if not dt.is_valid(row):
					invalid_lines += 1
					valid = False
					break
			if valid:
				valid_lines += 1
		if filter_data:
			if frequency == "hourly":
				if invalid_lines > 500:
					continue
			if frequency == "subhourly":
				if invalid_lines > 6000:
					continue
		metadata_row = []
		metadata_row.append(frequency) # str
		metadata_row.append(year) # int
		metadata_row.append(s) # str
		metadata_row.append(line_count) # int
		metadata_row.append(valid_lines) # int
		metadata_row.append(invalid_lines) # int
		#TODO: write each row with csv instead of putting everything in dictionary
		with open(csv_path, 'a') as f:
			writer = csv.writer(f)
			writer.writerow(metadata_row)


def sort_metadata(data):
	""" Tested """
	sorted_data = sorted(data, cmp=sort_by_year_validCount_name)
	return sorted_data


def sort_by_year_validCount_name(e1, e2):
	# sort by year first
	if e1[1] == e2[1]: # years are equal
		if e1[4] == e2[4]: # valid counts are equal
			if e1[2] < e2[2]:
				return -1
			else:
				return 1
		elif e1[4] < e2[4]:
			return 1
		else:
			return -1
	elif e1[1] < e2[1]:
		return -1
	else:
		return 1


def merge_dictionaries(d1, d2):
	""" Tested """
	merged = {}
	for key in d1:
		if key in d2:
			copy = [val for val in d1[key]]
			copy.extend(d2[key])
			merged[key] = copy
	return merged


def get_uscrn_dictionary(csv_path):
	data = {}
	with open(csv_path) as f:
		reader = csv.reader(f)
		reader.next() # skip the header row
		for line in reader:
			station_name = line[2]
			data[station_name] = line
	return data


if __name__ == "__main__":
	"""Just do one year at a time."""
	year = 2018
	filter_data = False
	if filter_data:
		h_filename = "{}-hourly-filtered.csv".format(year)
		sh_filename = "{}-subhourly-filtered.csv".format(year)
		merged_filename = "{}-merged-filtered.csv".format(year)
	else:
		h_filename = "{}-hourly-raw.csv".format(year)
		sh_filename = "{}-subhourly-raw.csv".format(year)
		merged_filename = "{}-merged-raw.csv".format(year)
	hourly_csv_path = os.path.join(os.path.dirname(__file__), h_filename)
	subhourly_csv_path = os.path.join(os.path.dirname(__file__), sh_filename)
	merged_csv_path = os.path.join(os.path.dirname(__file__), merged_filename)
	### Get data or not
	#write_uscrn_metadata(year, stations, "hourly", hourly_csv_path, filter_data)
	#write_uscrn_metadata(year, stations, "subhourly", subhourly_csv_path, filter_data)
	### Get data or not
	d1 = get_uscrn_dictionary(hourly_csv_path)
	d2 = get_uscrn_dictionary(subhourly_csv_path)
	merged = merge_dictionaries(d1, d2)
	metadata = sort_metadata(merged.values())
	with open(merged_csv_path, 'w') as f:
		writer = csv.writer(f)
		writer.writerow(["Frequency", "Year", "Station Name", "Total Lines", "Valid Lines", "Invalid Lines", "Frequency", "Year", "Station Name", "Total Lines", "Valid Lines", "Invalid Lines"])
		writer.writerows(metadata)