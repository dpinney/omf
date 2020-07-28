'''
Backend for fire map work.
'''

import multiprocessing, time
from flask import Flask
import json
from omf.weather import getSubGridData

app = Flask(__name__)

@app.route('/')
def root():
	return open('satellitemap_editablePopup.html').read()

@app.route('/test')
def test():
	x = 1 + 2
	return '<b>bold world</b> ' + str(x)

@app.route('/firedata/<lat>/<lon>/<dist>/<resolution>')
def firedata(lat, lon, dist, resolution):
	# x = omf.weather.get_ndfd(33,53)
	print(lat, lon, dist, resolution)
	# note: these inputs take precedence over url in js GET request
	# lat = 40.758701
	# lon = -111.876183
	# dist = 20
	# resolution = 20
	x = getSubGridData(str(lat), str(lon), str(dist), str(dist), str(resolution))
	print (json.dumps(x))
	print(type(json.dumps(x))) # x is a python dictionary, json.dumps is a string
	return json.dumps(x)

#FRONTEND JAVASCRIPT
# Sending requests from the frontend: https://www.w3schools.com/xml/ajax_xmlhttprequest_send.asp
# Example:
# var xhttp = new XMLHttpRequest();
# xhttp.open("GET", "firedata/33,44", false);
# xhttp.send();
# console.log(xhttp.responseText);

"""
This is sample stuff we want to put in front end

<!DOCTYPE html>
<html>
<body>

<div id="demo">
<h2>The XMLHttpRequest Object</h2>
<button type="button" onclick="loadDoc()">Change Content</button>
</div>

<script>
function loadDoc() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (this.readyState == 4 && this.status == 200) {
      document.getElementById("demo").innerHTML =
      this.responseText;
    }
  };
  xhttp.open("GET", "ajax_info.txt", true);
  xhttp.send();
}
</script>

</body>
</html>

"""

if __name__ == '__main__':
	app.run(debug=True)
