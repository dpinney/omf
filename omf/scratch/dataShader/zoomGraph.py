import math
import numpy as np
import pandas as pd
import json

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout
from datashader.bundling import connect_edges

#from itertools import chain

#dash imports
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#plotly import
import plotly

app = dash.Dash(__name__)

np.random.seed(0)
n=100000
m=20000

nodes = pd.DataFrame(["node"+str(i) for i in range(n)], columns=['name'])
#nodes.tail()
edges = pd.DataFrame(np.random.randint(0,len(nodes), size=(m, 2)),
                     columns=['source', 'target'])
#edges.tail()

randomloc = random_layout(nodes)
#randomloc.tail()

cvsopts = dict(plot_height=900, plot_width=1200)

#Creates nodes in datasahder image
def nodesplot(nodes, name=None, canvas=None, cat=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    aggregator=None if cat is None else ds.count_cat(cat)
    agg=canvas.points(nodes,'x','y',aggregator)
    return tf.spread(tf.shade(agg, cmap=["#FF3333"]), px=3, name=name)

forcedirected = random_layout(nodes, edges)

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
    #print(np)
    ep = edgesplot(edges, name + " edges", canvas)
    #print(ep)
    return tf.stack(ep, np, how="over", name=name)

fd = forcedirected
fd_d = graphplot(fd, connect_edges(fd,edges)) 

#convert datashder image to png
back_img = tf.Image(fd_d).to_pil()


x_range=fd.x.min(), fd.x.max()
y_range=fd.y.min(), fd.y.max()

#xr = nodes.x.min(), nodes.x.max()
#yr = nodes.y.min(), nodes.y.max()
plot_height=900
plot_width=1200


#Create initial plotly graph with datashader image as background
import plotly.graph_objs as go
f = go.Figure(data=[{'x': x_range, 
                           'y': y_range, 
                           'mode': 'markers',
                           'marker': {'opacity': 0}}], # invisible trace to init axes and to support autoresize
                    layout={'width': plot_width, 
                            'height': plot_height}
                   )

f.layout.images = [go.layout.Image(
    source = back_img,  # plotly now performs auto conversion of PIL image to png data URI
    xref = "x",
    yref = "y",
    x = x_range[0],
    y = y_range[1],
    sizex = x_range[1] - x_range[0],
    sizey = y_range[1] - y_range[0],
    #sizing = "stretch",
    layer = "below")]

#Fucntion for creating new plotly graph when zooming
def newPlotlyGeneration(relayoutData):
    f = go.Figure(data=[{'x': [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']], 
                           'y': [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']], 
                           'mode': 'markers',
                           'marker': {'opacity': 0}}], # invisible trace to init axes and to support autoresize
                    layout={'width': 1200, 
                            'height': 900}
                   )
    newImg = newGraphplot(fd, connect_edges(fd,edges), x_range=[relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']], y_range=[relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']])
    newPil = tf.Image(newImg).to_pil()
    #in_mem_file = io.BytesIO()
    #newPil.save(in_mem_file, format = "PNG")
    # reset file pointer to start
    #in_mem_file.seek(0)
    #img_bytes = in_mem_file.read()
    #base64_encoded_result_bytes = base64.b64encode(img_bytes)
    #base64_encoded_result_str = base64_encoded_result_bytes.decode('ascii')

    f.layout.images = [go.layout.Image(
        source = newPil,  # plotly now performs auto conversion of PIL image to png data URI
        xref = "x",
        yref = "y",
        x = relayoutData['xaxis.range[0]'],
        y = relayoutData['yaxis.range[1]'],
        sizex = relayoutData['xaxis.range[1]'] - relayoutData['xaxis.range[0]'],
        sizey = relayoutData['yaxis.range[1]'] - relayoutData['yaxis.range[0]'],
        #sizing = "stretch",
        layer = "below")]
    return f

#Function to create new datashader image, used in newPlotlyGeneration
def newGraphplot(nodes, edges, name="", canvas=None, cat=None, x_range=None, y_range=None):
    if canvas is None:
        xr = x_range
        yr = y_range
        canvas = ds.Canvas(x_range=xr, y_range=yr, **cvsopts)
    #print(x_range)
    np = nodesplot(nodes, name + " nodes", canvas, cat)
    #print(np)
    ep = edgesplot(edges, name + " edges", canvas)
    #print(ep)
    return tf.stack(ep, np, how="over", name=name)


app.layout = html.Div([
    html.Div(
        dcc.Graph(
            id='g1',
            config={'displayModeBar': False}
        ), className='four columns'
    )
], className='row')


def highlight():
    def callback(relayoutData):
        try:
            newFig = newPlotlyGeneration(relayoutData)
            return newFig
        except (TypeError, KeyError) as e:
            newFig = go.Figure(data=[{'x': x_range, 
                               'y': y_range, 
                               'mode': 'markers',
                               'marker': {'opacity': 0}}], # invisible trace to init axes and to support autoresize
                        layout={'width': plot_width, 
                                'height': plot_height}
                       )

            newFig.layout.images = [go.layout.Image(
                source = back_img,
                xref = "x",
                yref = "y",
                x = x_range[0],
                y = y_range[1],
                sizex = x_range[1] - x_range[0],
                sizey = y_range[1] - y_range[0],
                #sizing = "stretch",
                layer = "below")]
            return newFig

    return callback



# app.callback is a decorator which means that it takes a function
# as its argument.
# highlight is a function "generator": it's a function that returns function
app.callback(
    Output('g1', 'figure'),
    [Input('g1', 'relayoutData')]
)(highlight())

if __name__ == '__main__':
    app.run_server(debug=True)