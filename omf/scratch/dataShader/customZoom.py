import math, json, io, base64, param
import numpy as np
import pandas as pd
import gc

from flask import Flask, render_template, redirect, request

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout, LayoutAlgorithm
from datashader.bundling import connect_edges

app = Flask(__name__)

@app.route("/")
def hello():
	return "Hello World!"

@app.route("/testing", methods=["GET", "POST"])
def testingRoute(x_range=(40,50), y_range=(40,50)):
	if request.method == 'POST':
		#add in calc for current dimensions of canvas?
		#counter=request.form.get("counter", type=float) * .5
		#print(counter)
		#x_click = request.form.get("x_click", type=float)
		#y_click = abs(request.form.get("y_click", type=float) - cvsopts['plot_height'])
		#y_click = abs(request.form.get("y_click", type=float))
		#current_x_range = tuple((request.form.get("x_low", type=float), request.form.get("x_high", type=float)))
		#current_y_range = tuple((request.form.get("y_low", type=float), request.form.get("y_high", type=float)))
		#print(current_x_range)
		#print(current_y_range)
		#x_click, y_click = vectorCalc(current_x_range, current_y_range, x_click, y_click)
		# p(t) = a*(1-t) + b*t 
		x_low = request.form.get("x_low", type=float)
		y_low = request.form.get("y_low", type=float)
		x_high = request.form.get("x_high", type=float)
		y_high = request.form.get("y_high", type=float)
		#x_high = min(x_click+(counter), 1)
		#y_high = min(y_click +(counter), 1)
		x_range = (x_low, x_high)
		y_range = (y_low, y_high)
	#print(current_x_range)
	dsPlot = newGraphplot(randomloc, connect_edges(randomloc,edges), x_range=x_range, y_range=y_range)
	#convert datashder image to png
	back_img = tf.Image(dsPlot).to_pil()
	in_mem_file = io.BytesIO()
	back_img.save(in_mem_file, format = "PNG")
	# reset file pointer to start
	in_mem_file.seek(0)
	img_bytes = in_mem_file.read()
	base64_encoded_result_bytes = base64.b64encode(img_bytes)
	base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')
	return render_template("testRoute.html", image=base64_encoded_result_str, x_range=x_range, y_range=y_range, x_low=x_range[0], x_high=x_range[1], y_low=x_range[0], y_high=y_range[1])

def vectorCalc(x_range, y_range, x_click, y_click):
	x_click = x_range[0]*(1-x_click/cvsopts['plot_width']) + x_range[1]*(x_click/cvsopts['plot_width'])
	y_click = y_range[0]*(1-y_click/cvsopts['plot_height']) + y_range[1]*(y_click/cvsopts['plot_height'])
	return x_click, y_click

@app.route("/changeRange", methods=["POST"])
def changeRange():
	x_range = request.form.get("x_range")
	y_range = request.form.get("y_range")
	return jsonify("/testing")

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
        points = np.asarray(np.random.uniform(low=40, high=50, size=(len(df), 2)))

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

cvsopts = dict(plot_height=756, plot_width=756)

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