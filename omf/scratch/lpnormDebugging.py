'''
# Small little function to calculate scaling factor for a line.
import math
x1 = 586.094375282
y1 = 445.866492772
x2 = 589.462214662
y2 = 442.843846618
z = 57.339599609375
if __name__ == '__main__':
	print (math.sqrt(pow((x2-x1),2) + pow((y2-y1),2)))/z
'''

# Getting two images to show up on the same matplotlib object and scaled appropriately.
from matplotlib import pyplot as plt
import numpy as np
import networkx as nx
heatMap = plt.imshow(
	np.random.rand(5, 5),
	cmap = 'hot',
	interpolation = 'nearest',
	extent = [0,1,0,1],
	aspect='auto')
# draw networkx graph
#plt.gca().invert_yaxis() This isn't needed anymore?
plt.title("Hazard Field")
plt.show()