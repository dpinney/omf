import math, json, io, base64, param
import numpy as np
import pandas as pd
import gc

from flask import Flask, render_template, redirect, request, jsonify, url_for

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout, LayoutAlgorithm
from datashader.bundling import connect_edges

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World!"

@app.route("/testing", methods=["GET", "POST"])
def testingRoute():
	return render_template("testRoute.html", x_low=xMin, y_low=yMin, x_high=xMax, y_high=yMax)

def vectorCalc(x_range, y_range, x_click, y_click):
	x_click = x_range[0]*(1-x_click) + x_range[1]*(x_click)
	y_click = y_range[0]*(1-y_click) + y_range[1]*(y_click)
	return x_click, y_click

@app.route("/mapResize", methods=["POST"])
def zoomButton():

	jsonResp = request.get_json()
	cvsopts['plot_height'] = int(jsonResp["height"])
	cvsopts['plot_width'] = int(jsonResp["width"])
	current_x_range = tuple((float(jsonResp["current_x_low"]), float(jsonResp["current_x_high"])))
	current_y_range = tuple((float(jsonResp["current_y_low"]), float(jsonResp["current_y_high"])))
	current_y_low, current_y_high = current_y_range[0], current_y_range[1]
	current_x_low, current_x_high = current_x_range[0], current_x_range[1]

	dsPlot = newGraphplot(randomloc, connect_edges(randomloc,edges), x_range=current_x_range, y_range=current_y_range)
	#convert datashder image to png
	back_img = tf.Image(dsPlot).to_pil()
	in_mem_file = io.BytesIO()
	back_img.save(in_mem_file, format = "PNG")
	# reset file pointer to start
	in_mem_file.seek(0)
	img_bytes = in_mem_file.read()
	base64_encoded_result_bytes = base64.b64encode(img_bytes)
	base64_encoded_result_str = 'data:image/png;base64,' + base64_encoded_result_bytes.decode('ascii')
	return jsonify(newImage=base64_encoded_result_str, x_low=current_x_range[0], y_low=current_y_range[0], x_high=current_x_range[1], y_high=current_y_range[1])

class map_layout(LayoutAlgorithm):
    """
    Custom layout function for testing different scenarios with positions for node and edges layout

    Accepts an edges argument for consistency with other layout algorithms,
    but ignores it.
    """

    def __call__(self, nodes, edges=None, **params):
        p = param.ParamOverrides(self, params)

        np.random.seed(p.seed)

        df = nodes.copy()
        points = np.asarray(np.random.uniform(low=-115, high=-105, size=(len(df), 1)))
        pointsy = np.asarray(np.random.uniform(low=30, high=40, size=(len(df), 1)))

        df[p.x] = points[:, 0]
        df[p.y] = pointsy[:, 0]

        return df

np.random.seed(0)
n=100000
m=200000

nodes = pd.DataFrame(["node"+str(i) for i in range(n)], columns=['name'])
edges = pd.DataFrame(np.random.randint(0,len(nodes), size=(m, 2)), columns=['source', 'target'])

randomloc = map_layout(nodes,edges)
#print(randomloc.tail())
xMin = randomloc['x'].min()
yMin = randomloc['y'].min()
xMax = randomloc['x'].max()
yMax = randomloc['y'].max()

cvsopts = dict(plot_height=900, plot_width=1900)

#creaes nodes in datashader image
def nodesplot(nodes, name=None, canvas=None, cat=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    aggregator=None if cat is None else ds.count_cat(cat)
    agg=canvas.points(nodes,'x','y',aggregator)
    return tf.spread(tf.shade(agg, cmap=["#FF3333"]), px=3, name=name)

#creates edges in datashader image
def edgesplot(edges, name=None, canvas=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    return tf.shade(canvas.line(edges, 'x','y', agg=ds.count()), name=name)
   
#combines nodes and edges in datashader image 
def graphplot(nodes, edges, name="", canvas=None, cat=None):
    if canvas is None:
        xr = nodes.x.min(), nodes.x.max()
        yr = nodes.y.min(), nodes.y.max()
        canvas = ds.Canvas(x_range=xr, y_range=yr, **cvsopts)
        
    np = nodesplot(nodes, name + " nodes", canvas, cat)
    ep = edgesplot(edges, name + " edges", canvas)
    return tf.stack(ep, np, how="over", name=name)

def newGraphplot(nodes, edges, name="", canvas=None, cat=None, x_range=None, y_range=None):
    if canvas is None:
        xr = x_range
        yr = y_range
        canvas = ds.Canvas(x_range=xr, y_range=yr, **cvsopts)
    np = nodesplot(nodes, name + " nodes", canvas, cat)
    #print("nodes")
    ep = edgesplot(edges, name + " edges", canvas)
    #print("edges")
    return tf.stack(ep, np, how="over", name=name)

if __name__ == '__main__':
	app.run(debug=False)