import requests, tempfile, io, subprocess
from zipfile import ZipFile

#https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/

#longitude max = 180W
#longitude min = 043W
#try +/- 5 for the
#latitude min = 10N
#latitude max = 60N
for lat in range(10, 61):
	for lon in range(43, 180):
		print(lat,lon)

response = requests.get("https://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/N45W079.hgt.zip")

print(response.status_code)
with tempfile.TemporaryFile() as tmp:
	tmp.write(response.content)
	with ZipFile(tmp, 'r') as zipper:
		zipper.extractall('../hgtFiles')
		args = ["srtm2sdf", "../hgtFiles/N45W079.hgt"]
		subprocess.Popen(args).wait()