function convertToGeoJSON(inputArray) {
	var props = inputArray[0];
	var geojsonArray = [];
	for (var i = 1; i < inputArray.length; i++) {
		var latitude = item[0];
		var longitude = item[1];
		var geojsonFeature = {
			"type":"Feature",
			"properties": {},
			"geometry": {
				"type":"Point",
				"coordinates": [latitude, longitude]
			}
		};
		if (props.length > 2) {
			var props2 = props.slice(2);
			for (var x=0; x<props2.length; x++) {
				geojsonFeature["properties"][props2[x]] = item[x];
			}
		}
		geojsonArray.push(geojsonFeature);
	}
	return geojsonArray;
}