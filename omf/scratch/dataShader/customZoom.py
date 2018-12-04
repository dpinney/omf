import math, json, io, base64, param
import numpy as np
import pandas as pd
import gc

from flask import Flask, render_template, redirect, request, jsonify

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout, LayoutAlgorithm
from datashader.bundling import connect_edges

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World!"

@app.route("/testing", methods=["GET", "POST"])
def testingRoute(x_range=(0,1), y_range=(0,1)):
	dsPlot = newGraphplot(randomloc, connect_edges(randomloc,edges), x_range=x_range, y_range=y_range)
	#convert datashder image to png
	back_img = tf.Image(dsPlot).to_pil()
	in_mem_file = io.BytesIO()
	back_img.save(in_mem_file, format = "PNG")
	# reset file pointer to start
	in_mem_file.seek(0)
	img_bytes = in_mem_file.read()
	base64_encoded_result_bytes = base64.b64encode(img_bytes)
	base64_encoded_result_str = 'data:image/png;base64,' + base64_encoded_result_bytes.decode('ascii')
	return render_template("testRoute.html", newImage=base64_encoded_result_str, x_low=0, y_low=0, x_high=1, y_high=1)

def vectorCalc(x_range, y_range, x_click, y_click):
	x_click = x_range[0]*(1-x_click) + x_range[1]*(x_click)
	print(x_range[1]*(x_click))
	y_click = y_range[0]*(1-y_click) + y_range[1]*(y_click)
	return x_click, y_click

@app.route("/changeRange", methods=["POST"])
def changeRange():
	jsonResp = request.get_json()
	x_low = float(jsonResp["x_low"])
	print(x_low)
	y_low = float(jsonResp["y_low"])
	x_high = float(jsonResp["x_high"])
	y_high = float(jsonResp["y_high"])
	#x_high = min(x_click+(counter), 1)
	#y_high = min(y_click +(counter), 1)
	x_range = (x_low, x_high)
	y_range = (y_low, y_high)
	dsPlot = newGraphplot(randomloc, connect_edges(randomloc,edges), x_range=x_range, y_range=y_range)
	#convert datashder image to png
	back_img = tf.Image(dsPlot).to_pil()
	in_mem_file = io.BytesIO()
	back_img.save(in_mem_file, format = "PNG")
	# reset file pointer to start
	in_mem_file.seek(0)
	img_bytes = in_mem_file.read()
	base64_encoded_result_bytes = base64.b64encode(img_bytes)
	base64_encoded_result_str = 'data:image/png;base64,' + base64_encoded_result_bytes.decode('ascii')
	return jsonify(newImage=base64_encoded_result_str)

@app.route("/zoom", methods=["POST"])
def zoom():
	#print(request.get_json())
	jsonResp = request.get_json()
	print(jsonResp)
	#Get the clicks
	x_down = float(jsonResp["x_down"])
	y_down = 1 - float(jsonResp["y_down"])
	x_up = float(jsonResp["x_up"])
	y_up = 1 - float(jsonResp["y_up"])
	#Translate from clicks to min/max
	x_low = min(x_down, x_up)
	y_low = min(y_down, y_up)
	x_high = max(x_down, x_up)
	y_high = max(y_down, y_up)
	#Get the old range
	print((float(jsonResp["current_x_low"])))
	print(type((float(jsonResp["current_x_low"]))))
	current_x_range = tuple((float(jsonResp["current_x_low"]), float(jsonResp["current_x_high"])))
	current_y_range = tuple((float(jsonResp["current_y_low"]), float(jsonResp["current_y_high"])))
	#Vectorizeto fit range
	x_low, y_low = vectorCalc(current_x_range, current_y_range, x_low, y_low)
	x_high, y_high = vectorCalc(current_x_range, current_y_range, x_high, y_high)

	x_range = (x_low, x_high)
	y_range = (y_low, y_high)
	print(x_range, y_range)
	dsPlot = newGraphplot(randomloc, connect_edges(randomloc,edges), x_range=x_range, y_range=y_range)
	#convert datashder image to png
	back_img = tf.Image(dsPlot).to_pil()
	in_mem_file = io.BytesIO()
	back_img.save(in_mem_file, format = "PNG")
	# reset file pointer to start
	in_mem_file.seek(0)
	img_bytes = in_mem_file.read()
	base64_encoded_result_bytes = base64.b64encode(img_bytes)
	base64_encoded_result_str = 'data:image/png;base64,' + base64_encoded_result_bytes.decode('ascii')
	return jsonify(newImage=base64_encoded_result_str, x_low=x_low, y_low=y_low, x_high=x_high, y_high=y_high)

class map_layout(LayoutAlgorithm):
    """
    Assign coordinates to the nodes randomly.

    Accepts an edges argument for consistency with other layout algorithms,
    but ignores it.
    """

    def __call__(self, nodes, edges=None, **params):
        p = param.ParamOverrides(self, params)

        np.random.seed(p.seed)

        df = nodes.copy()
        points = np.asarray(np.random.uniform(low=0, high=1, size=(len(df), 2)))

        df[p.x] = points[:, 0]
        df[p.y] = points[:, 1]

        return df

np.random.seed(0)
n=100000
m=200000

nodes = pd.DataFrame(["node"+str(i) for i in range(n)], columns=['name'])
edges = pd.DataFrame(np.random.randint(0,len(nodes), size=(m, 2)), columns=['source', 'target'])

randomloc = map_layout(nodes,edges)
print(randomloc.tail())
#how to add to resize function

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