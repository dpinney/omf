#!/usr/bin/env python
# coding: utf-8

# In[1]:


import math
import numpy as np
import pandas as pd

import datashader as ds
import datashader.transfer_functions as tf
from datashader.layout import random_layout, circular_layout, forceatlas2_layout
from datashader.bundling import connect_edges, hammer_bundle

from itertools import chain

#dash
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

#from example
import json
import copy
import xarray as xr
from collections import OrderedDict
from textwrap import dedent as d

# In[2]:
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}


np.random.seed(0)
n=100
m=200

nodes = pd.DataFrame(["node"+str(i) for i in range(n)], columns=['name'])
nodes.tail()
edges = pd.DataFrame(np.random.randint(0,len(nodes), size=(m, 2)),
                     columns=['source', 'target'])
edges.tail()

randomloc = random_layout(nodes)
randomloc.tail()

cvsopts = dict(plot_height=600, plot_width=800)

def nodesplot(nodes, name=None, canvas=None, cat=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    aggregator=None if cat is None else ds.count_cat(cat)
    agg=canvas.points(nodes,'x','y',aggregator)
    return tf.spread(tf.shade(agg, cmap=["#FF3333"]), px=3, name=name)

forcedirected = random_layout(nodes, edges)

def edgesplot(edges, name=None, canvas=None):
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    return tf.shade(canvas.line(edges, 'x','y', agg=ds.count()), name=name)
    
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

back_img = tf.Image(fd_d).to_pil()

x_range=fd.x.min(), fd.x.max()
y_range=fd.y.min(), fd.y.max()

#xr = nodes.x.min(), nodes.x.max()
#yr = nodes.y.min(), nodes.y.max()
plot_height=600
plot_width=800

mapbox_access_token = 'pk.eyJ1IjoiZWp0YWxib3QiLCJhIjoiY2ptMHBlOGdjMmZlaTNwb2dwMHE2Mm54NCJ9.xzceVNmAZy49SyFDb3UMaw'

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

flaskServer = flask.Flask(__name__)
app = dash.Dash(__name__, server=flaskServer)

app.layout = html.Div([
            dcc.Graph(
                id = 'graph-1',
                figure = f,
                config = {
                    'doubleClick': 'reset'
                }
            ),
            
            html.Div([
            dcc.Markdown(d("""
                **Zoom and Relayout Data**

                Click and drag on the graph to zoom or click on the zoom
                buttons in the graph's menu bar.
                Clicking on legend items will also fire
                this event.
            """)),
            html.Pre(id='relayout-data', style=styles['pre']),
        ], className='three columns')

        ])

#f


# In[11]:

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

#newG = newGraphPlot(fd, connect_edges(fd,edges), "Force-directed", x_range=x_range, y_range=y_range, plot_width=plot_width, plot_height=plot_height)

#print(newG)

#newImg = tf.Image(newG).to_pil()

@app.callback(
    Output('relayout-data', 'children'),
    [Input('graph-1', 'relayoutData')])
def display_selected_data(relayoutData):
    return json.dumps(relayoutData, indent=2)

#@app.callback(
#	dash.dependencies.Output(),
#	[dash.dependencies.Input()])

@app.callback(
    Output('graph-1', 'figure'),
    [Input('graph-1', 'relayoutData')])
def update_ds_image(layout, x_range, y_range, plot_width, plot_height):
    img = f.layout.images[0]
    
    # Update with batch_update so all updates happen simultaneously

    img.x = x_range[0]
    img.y = y_range[1]
    img.sizex = x_range[1] - x_range[0]
    img.sizey = y_range[1] - y_range[0]
    #update the image source here, rest can stay
    newDataShade = newGraphplot(fd, connect_edges(fd,edges), x_range=x_range, y_range=y_range)
    img.source = tf.Image(newDataShade).to_pil()
    return f

#f.layout.on_change(update_ds_image, 'xaxis.range', 'yaxis.range', 'width', 'height')
#newImg


# In[12]:


mapbox_access_token = 'pk.eyJ1IjoiZWp0YWxib3QiLCJhIjoiY2ptMHBlOGdjMmZlaTNwb2dwMHE2Mm54NCJ9.xzceVNmAZy49SyFDb3UMaw'

map_figure = go.Figure(data=[go.Scattermapbox(
    lat=[fd.x.min(), fd.x.max()],
    lon=[fd.y.min(), fd.y.max()],
    mode='markers')], 
                    # invisible trace to init axes and to support autoresize
                    layout={'width': plot_width, 
                            'height': plot_height,
                            'autosize': True,
                            'mapbox':{
                               'accesstoken': mapbox_access_token,
                               'bearing': 0,
                               'center': {
                                   'lat': 0,
                                   'lon': -0
                                },
                               'pitch': 0,
                            }
                    })

map_figure.layout.images = [go.layout.Image(
    source = back_img,  # plotly now performs auto conversion of PIL image to png data URI
    xref = "paper",
    yref = "paper",
    x = x_range[0],
    y = y_range[1],
    sizex = x_range[1] - x_range[0],
    sizey = y_range[1] - y_range[0],
    #sizing = "stretch",
    layer = "above")]

print(map_figure)
#map_figure.layout.on_change(update_ds_image, 'xaxis.range', 'yaxis.range', 'width', 'height')

#map_figure

if __name__ == '__main__':
    flaskServer.run(debug=True)