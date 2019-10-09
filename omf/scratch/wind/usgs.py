import requests, json

#authentication
authparams = json.dumps({
	"username": "",
	"password": "",
	"authType": "EROS",
	"catalogId": "EE"
})

jsonreq = {
	"jsonRequest": authparams
}

auth_url = "https://earthexplorer.usgs.gov/inventory/json/v/1.4.0/login"

resp = requests.post(auth_url, data=jsonreq)

api_key = resp.json().get('data')

#searching datasets - one example but rest follow this

dataset_search_params = {
	"datasetName": "LANDSAT_8",
	"spatialFilter": {
		"filterType": "mbr",
		"lowerLeft": {
				"latitude": 44.60847,
				"longitude": -99.69639
		},
		"upperRight": {
				"latitude": 44.60847,
				"longitude": -99.69639
		}
	},
	"temporalFilter": {
		"startDate": "2019-09-01",
		"endDate": "2019-10-01"
	},
	"apiKey": api_key
}

jsonreq = {
	"jsonRequest": json.dumps(dataset_search_params)
}

resp = requests.get("https://earthexplorer.usgs.gov/inventory/json/v/1.4.0/datasets", params=jsonreq)
print(resp.json())