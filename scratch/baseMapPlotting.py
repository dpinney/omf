''' Draw America. '''

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# Lambert Conformal Conic map.
m = Basemap(llcrnrlon=--80.05067825317383,
			llcrnrlat=38.39379044654673,
			urcrnrlon=-79.96004104614258,
			urcrnrlat=38.4377914419658,
			projection='lcc',
			lat_1=20.,
			lat_2=40.,
			lon_0=-60.,
			resolution ='l',
			area_thresh=1000.)
m.drawcoastlines()
m.drawcountries()
m.drawstates()
m.drawmapboundary(fill_color='#99ffff')
m.fillcontinents(color='#cc9966' ,lake_color='#99ffff')
m.drawparallels(np.arange(10,70,20), labels=[1,1,0,0])
m.drawmeridians(np.arange(-100,0,20), labels=[0,0,0,1])
plt.title('Hello Basemap')

''' Getting image from OSM to show map features. '''

import urllib
fname, headers = urllib.urlretrieve('http://render.openstreetmap.org/cgi-bin/export?bbox=-80.05067825317383,38.39379044654673,-79.96004104614258,38.4377914419658&scale=27116&format=png', filename='test.png')
print 'Downloaded file:', fname
im = plt.imread(fname)
	
m.imshow(im, interpolation='lanczos', origin='upper')
plt.show()

#TODO: make the lat/lon coordinates agree. Because clearly the current behavior is wacky.