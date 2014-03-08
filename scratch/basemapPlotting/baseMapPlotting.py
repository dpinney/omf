''' Draw America. '''

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import maskoceans
from random import uniform, choice

# Lambert Conformal Conic map.
# create polar stereographic Basemap instance.
m = Basemap(projection='merc',
			lon_0=-95,
			lat_0=35,
            llcrnrlat=20,
            urcrnrlat=50,
            llcrnrlon=-130,
            urcrnrlon=-60,
            rsphere=6371200.,
            resolution='l',
            area_thresh=10000)
# draw coastlines, state and country boundaries, edge of map.
m.drawcoastlines()
m.drawstates()
m.drawcountries()

# # Getting image from OSM to show map features. 
# import urllib2
# fname, headers = urllib2.urlretrieve('http://render.openstreetmap.org/cgi-bin/export?bbox=-80.05067825317383,38.39379044654673,-79.96004104614258,38.4377914419658&scale=27116&format=png', filename='test.png')
# print 'Downloaded file:', fname
# im = plt.imread(fname)
# m.imshow(interpolation='lanczos', origin='upper')
# #TODO: make the lat/lon coordinates agree. Because clearly the current behavior is wacky.

randPoints = [(uniform(-130,-60),uniform(20,50),uniform(5,45),choice(['red','blue','green'])) for x in range(90)]
lons = [p[0] for p in randPoints]
lats = [p[1] for p in randPoints]
sizes = [p[2] for p in randPoints]
colors = [p[3] for p in randPoints]

# # Try a scatter plot
# m.scatter(lons, lats, latlon=True, c=colors, s=sizes)
# # Try a mesh
# m.pcolor(lons, lats, sizes, latlon=True, tri=True)

# Try a TMY2 Scatter Plot.
from tmy2Wrangling import points
lons = [p[0] for p in points]
lats = [p[1] for p in points]
sizes = [p[2] for p in points]

m.scatter(lons, lats, latlon=True, c='red', s=sizes)

# Output
plt.show()

