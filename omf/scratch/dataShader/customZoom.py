import math, json, io, base64
import numpy as np
import pandas as pd

from flask import Flask, render_template

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout
from datashader.bundling import connect_edges

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World!"

@app.route("/testing")
def testingRoute():
	np.random.seed(0)
	n=100000
	m=200000

	nodes = pd.DataFrame(["node"+str(i) for i in range(n)], columns=['name'])
	edges = pd.DataFrame(np.random.randint(0,len(nodes), size=(m, 2)), columns=['source', 'target'])

	randomloc = random_layout(nodes,edges)

	dsPlot = graphplot(randomloc, connect_edges(randomloc,edges)) 

	#convert datashder image to png
	back_img = tf.Image(dsPlot).to_pil()
	in_mem_file = io.BytesIO()
	back_img.save(in_mem_file, format = "PNG")
	# reset file pointer to start
	in_mem_file.seek(0)
	img_bytes = in_mem_file.read()
	base64_encoded_result_bytes = base64.b64encode(img_bytes)
	base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
	return render_template("testRoute.html", image=base64_encoded_result_bytes)

cvsopts = dict(plot_height=900, plot_width=1200)

def nodesplot(nodes, name=None, canvas=None, cat=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    aggregator=None if cat is None else ds.count_cat(cat)
    agg=canvas.points(nodes,'x','y',aggregator)
    return tf.spread(tf.shade(agg, cmap=["#FF3333"]), px=3, name=name)

#creates edges in datashader image
def edgesplot(edges, name=None, canvas=None):
    #print('Start edges', file=sys.stdout)
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    #print('Made canvas edges', file=sys.stdout)
    #print(ds.count())
    #print(canvas.line(edges, 'x','y', agg=ds.count()))
    return tf.shade(canvas.line(edges, 'x','y', agg=ds.count()), name=name)
   
#combines nodes and edges in datashader image 
def graphplot(nodes, edges, name="", canvas=None, cat=None):
    if canvas is None:
        xr = nodes.x.min(), nodes.x.max()
        yr = nodes.y.min(), nodes.y.max()
        canvas = ds.Canvas(x_range=xr, y_range=yr, **cvsopts)
        
    np = nodesplot(nodes, name + " nodes", canvas, cat)
    #print(np)
    ep = edgesplot(edges, name + " edges", canvas)
    #print(ep)
    return tf.stack(ep, np, how="over", name=name)

if __name__ == '__main__':
	app.run(debug=True)