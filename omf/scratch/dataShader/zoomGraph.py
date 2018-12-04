from __future__ import print_function
import math
import numpy as np
import pandas as pd
import json
import gc, sys

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

from textwrap import dedent as d
#plotly import
import plotly

#gc.collect()

app = dash.Dash(__name__)

np.random.seed(0)
n=1000000
#Getting to 100000 edges causes malloc and other memory issues after a few zooms
m=2000000

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
    print('Start edges', file=sys.stdout)
    canvas = ds.Canvas(**cvsopts) if canvas is None else canvas
    print('Made canvas edges', file=sys.stdout)
    print(ds.count())
    print(canvas.line(edges, 'x','y', agg=ds.count()))

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

#Function for creating new plotly graph when zooming
def newPlotlyGeneration(relayoutData):
    #gc.collect()
    print('Create plotly data', file=sys.stdout)
    f = go.Figure(data=[{'x': [relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']], 
                           'y': [relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']], 
                           'mode': 'markers',
                           'marker': {'opacity': 0}}], # invisible trace to init axes and to support autoresize
                    layout={'width': 1200, 
                            'height': 900}
                   )
    print('Create new image', file=sys.stdout)
    newImg = newGraphplot(fd, connect_edges(fd,edges), x_range=[relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']], y_range=[relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']])
    print('New image created', file=sys.stdout)
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
    print('Nodes plot created', file=sys.stdout)
    #print(np)
    #issue is here with edges
    ep = edgesplot(edges, name + " edges", canvas)
    print('Edges plot created', file=sys.stdout)
    #print(ep)
    return tf.stack(ep, np, how="over", name=name)

#Function for creating new plotly graph of mapbox type
def newMapboxGeneration(relayoutData):
    mapbox_access_token = 'pk.eyJ1IjoiZWp0YWxib3QiLCJhIjoiY2ptMHBlOGdjMmZlaTNwb2dwMHE2Mm54NCJ9.xzceVNmAZy49SyFDb3UMaw'

    map_figure = go.Figure(data=[go.Scattermapbox(
        lat=[1, 2],
        lon=[1, 2],
        mode='markers')], 
                        # invisible trace to init axes and to support autoresize
                        layout={'title': str(relayoutData['mapbox.zoom']) +" " +str(relayoutData['mapbox.center']['lat']),
                                'width': 1200, 
                                'height': 900,
                                #'autosize': True,
                                'mapbox':{
                                   'accesstoken': mapbox_access_token,
                                   'bearing': 0,
                                   'center': {
                                       'lat': relayoutData['mapbox.center']['lat'],
                                       'lon': relayoutData['mapbox.center']['lon']
                                    },
                                   'pitch': 0,
                                   'zoom': relayoutData['mapbox.zoom']
                                }
                        })
    
    #what to use to replace the xaxis values
    #newImg = newGraphplot(fd, connect_edges(fd,edges), x_range=[relayoutData['xaxis.range[0]'], relayoutData['xaxis.range[1]']], y_range=[relayoutData['yaxis.range[0]'], relayoutData['yaxis.range[1]']])
    #newPil = tf.Image(newImg).to_pil()
    
    map_figure.layout.images = [go.layout.Image(
        source = back_img,  # plotly now performs auto conversion of PIL image to png data URI
        #Need to figu
        xref = "paper",
        yref = "paper",
        #Sets the image's x position. How can this be set to reflect lat/lon
        x = 0,
        y = 1,
        #Sets the image container size horizontally. When `xref` is set to `paper`, units are sized relative to the plot width
        #How can image container reflect lat/lon?
        sizex = 1,
        sizey = 1,
        layer = "above")]
    return map_figure

app.layout = html.Div([
    html.Div(
        dcc.Graph(
            id='g1'
        ), className='four columns'
    ),
    html.Div(
        dcc.Graph(
            id='g2',
        ), className='four columns'
    ),
    html.Div([
    dcc.Markdown(d("""
        **Zoom and Relayout Data**

        Click and drag on the graph to zoom or click on the zoom
        buttons in the graph's menu bar.
        Clicking on legend items will also fire
        this event.
    """)),
    html.Pre(id='relayout-data'),
])
], className='row')


def zoomResize():
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

def mapResize():
    def callback(relayoutData):
        try:
            newFig = newMapboxGeneration(relayoutData)
            return newFig
        except (TypeError, KeyError) as e:
            mapbox_access_token = 'pk.eyJ1IjoiZWp0YWxib3QiLCJhIjoiY2ptMHBlOGdjMmZlaTNwb2dwMHE2Mm54NCJ9.xzceVNmAZy49SyFDb3UMaw'

            map_figure = go.Figure(data=[go.Scattermapbox(
                lat=x_range,
                lon=y_range,
                mode='markers')], 
                                # invisible trace to init axes and to support autoresize
                                layout={'width': plot_width, 
                                        'height': plot_height,
                                        #'autosize': True,
                                        'mapbox':{
                                           'accesstoken': mapbox_access_token,
                                           'bearing': 0,
                                           'center': {
                                               'lat': 0,
                                               'lon': -0
                                            },
                                           'pitch': 0,
                                           'zoom': 5
                                        }
                                })
            map_figure.layout.title = str(e)

            return map_figure

    return callback

#def coord_to_tile():
#    def callback(relayoutData):
#        lat_rad = math.radians(relayoutData['mapbox.center']['lat'])
#        n = 2.0 ** relayoutData['mapbox.zoom']
#        xtile = int((relayoutData['mapbox.center']['lon'] + 180.0) / 360.0 * n)
#        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
#        return ("X= " + str(xtile) + " Y= " +str(ytile))
#    return callback

tileSize = 256
def coord_to_tile():
    def callback(relayoutData):
        newCoordinates = {}
        newCoordinates['lat'] = relayoutData['mapbox.center']['lat']
        newCoordinates['lon'] = relayoutData['mapbox.center']['lon']
        newCoordinates['scale'] = relayoutData['mapbox.zoom']
        #world coordinates
        siny = math.sin(relayoutData['mapbox.center']['lat'] * math.pi / 180)
        siny = min(max(siny, -0.9999), 0.9999)
        newCoordinates['worldCoordinateX'] = tileSize * (0.5 + relayoutData['mapbox.center']['lon'] / 360)
        newCoordinates['worldCoordinateY'] =  tileSize * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) 
        #pixel coordinate 
        scale = 1.0 * 2**(relayoutData['mapbox.zoom'])
        newCoordinates['pixelCoordinateX'] = math.floor(newCoordinates['worldCoordinateX'] * scale)
        newCoordinates['pixelCoordinateY'] = math.floor(newCoordinates['worldCoordinateY'] * scale)
        #tilecoordinate
        newCoordinates['tilecoordinateX'] = math.floor(newCoordinates['worldCoordinateX'] * scale / tileSize)
        newCoordinates['tilecoordinateY'] = math.floor(newCoordinates['worldCoordinateY'] * scale / tileSize)
        return json.dumps(newCoordinates, indent=2)

    return callback

#def display_selected_data():
#    def callback(relayoutData):
#        return json.dumps(relayoutData, indent=2)
#    return callback


# app.callback is a decorator which means that it takes a function
# as its argument.
# highlight is a function "generator": it's a function that returns function
app.callback(
    Output('g1', 'figure'),
    [Input('g1', 'relayoutData')]
)(zoomResize())

app.callback(
    Output('g2', 'figure'),
    [Input('g2', 'relayoutData')]
)(mapResize())

app.callback(
    Output('relayout-data', 'children'),
    [Input('g2', 'relayoutData')]
)(coord_to_tile())
if __name__ == '__main__':
    app.run_server(debug=False)