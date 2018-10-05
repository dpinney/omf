# coding: utf-8
# A dash dashboard that employs datashader. Awesome!

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.plotly as py
import plotly.graph_objs as go
import datashader as ds
import datashader.transfer_functions as tf
import pandas as pd
import numpy as np
import json
import copy
import xarray as xr
from collections import OrderedDict

n = 1000000
max_points = 100000

np.random.seed(2)
cols = ['Signal'] # Column name of signal
start = 1456297053 # Start time
end = start + n # End time

# Generate a fake signal
time = np.linspace(start, end, n)
signal = np.random.normal(0, 0.3, size=n).cumsum() + 50

# Generate many noisy samples from the signal
noise = lambda var, bias, n: np.random.normal(bias, var, n)
data = {c: signal + noise(1, 10*(np.random.random() - 0.5), n) for c in cols}

# # Pick a few samples and really blow them out
locs = np.random.choice(n, 10)

# print locs
data['Signal'][locs] *= 2

# # Default plot ranges:
x_range = (start, end)
y_range = (1.2 * signal.min(), 1.2 * signal.max())

# Create a dataframe
data['Time'] = np.linspace(start, end, n)
df = pd.DataFrame(data)

time_start = df['Time'].values[0]
time_end = df['Time'].values[-1]

cvs = ds.Canvas(x_range = x_range, y_range=y_range)

aggs = OrderedDict((c, cvs.line(df, 'Time', c)) for c in cols)
img = tf.shade(aggs['Signal'])

arr = np.array(img)
z = arr.tolist()

# axes
dims = len(z[0]), len(z)

x = np.linspace(x_range[0], x_range[1], dims[0])
y = np.linspace(y_range[0], y_range[1], dims[0])

fig1 = {
    'data': [{
        'x': x,
        'y': y,
        'z': z,
        'type': 'heatmap',
        'showscale': False,
        'colorscale': [[0, 'rgba(255, 255, 255,0)'], [1, 'rgba(0,0,255,1)']]}],
    'layout': {
        'margin': {'t': 50, 'b': 20},
        'height': 250,
        'xaxis': {
            'showline': True,
            'zeroline': False,
            'showgrid': False,
            'showticklabels': True
        },
        'yaxis': {
            'fixedrange': True,
            'showline': False,
            'zeroline': False,
            'showgrid': False,
            'showticklabels': False,
            'ticks': ''
        },
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white'}
}

fig2 = {
    'data': [{
        'x': x,
        'y': y,
        'z': z,
        'type': 'heatmap',
        'showscale': False,
        'colorscale': [[0, 'rgba(255, 255, 255,0)'], [1, 'rgba(0,0,255,1)']]}],
    'layout': {
        'margin': {'t': 50, 'b': 20},
        'height': 250,
        'xaxis': {
            'fixedrange': True,
            'showline': True,
            'zeroline': False,
            'showgrid': False,
            'showticklabels': True
        },
        'yaxis': {
            'fixedrange': True,
            'showline': False,
            'zeroline': False,
            'showgrid': False,
            'showticklabels': False,
            'ticks': ''
        },
        'plot_bgcolor': 'white',
        'paper_bgcolor': 'white'}
}

app = dash.Dash()

server = app.server

app.layout = html.Div([
    html.Div([
        html.Div([
            html.H3('VISUALIZE MILLIONS OF POINTS WITH DATASHADER AND PLOTLY')
        ], className = "eight columns"),

        html.Div([
            html.Img(
                src=('https://s3-us-west-1.amazonaws.com/plotly-tutorials/'
                'logo/new-branding/dash-logo-by-plotly-stripe.png'),
                style={
                    'height': '100px',
                    'float': 'right'}),
        ], className = "four columns")
    ], className = "row"),

    html.Div([
        html.Div([
            html.Strong('Click and drag on the plot for high-res view of\
             selected data', id = 'header-1'),
            dcc.Graph(
                id = 'graph-1',
                figure = fig1,
                config = {
                    'doubleClick': 'reset'
                }
            )
        ], className = 'twelve columns')
    ], className ='row'),

    html.Div([
        html.Div([
            html.Strong('0 points selected', id = 'header-2'),
            dcc.Graph(
                id = 'graph-2',
                figure = fig2
            )
        ], className = 'twelve columns')
    ], className ='row'),

])

@app.callback(
    Output('header-2', 'children'),
    [Input('graph-1', 'relayoutData')])
def selectionRange(selection):
    if selection is not None and 'xaxis.range[0]' in selection and \
                                 'xaxis.range[1]' in selection:
        x0 = selection['xaxis.range[0]']
        x1 = selection['xaxis.range[1]']
        sub_df = df[(df.Time >= x0) & (df.Time <= x1)]
        num_pts = len(sub_df)
        if num_pts < max_points:
            number_print = "{2:,} points selected between {0:,.4} and {1:,.4}".\
            format(selection['xaxis.range[0]'], selection['xaxis.range[1]'],
            abs(int(selection['xaxis.range[1]']) - \
            int(selection['xaxis.range[0]'])))
        else:
            number_print = "{0:,} points selected. Select less than {1:}k \
            points to invoke high-res scattergl trace".format(
            abs(int(selection['xaxis.range[1]']) - \
            int(selection['xaxis.range[0]'])), (max_points/1000))
    else:
        number_print = "0 points selected"
    return number_print

@app.callback(
    Output('graph-2', 'figure'),
    [Input('graph-1', 'relayoutData')])
def selectionHighlight(selection):
    new_fig2 = fig2.copy()
    if selection is not None and 'xaxis.range[0]' in selection and \
                                 'xaxis.range[1]' in selection:
        x0 = selection['xaxis.range[0]']
        x1 = selection['xaxis.range[1]']
        sub_df = df[(df.Time >= x0) & (df.Time <= x1)]
        num_pts = len(sub_df)
        if num_pts < max_points:
            shape = dict(
                type = 'rect',
                xref = 'x',
                yref = 'paper',
                y0 = 0,
                y1 = 1,
                x0 = x0,
                x1 = x1,
                line = {
                    'color': 'rgba(255, 0, 0, 1)',
                    'width': 1,
                },
                fillcolor = 'rgba(255, 0, 0, 0.7)'
            )

            new_fig2['layout']['shapes'] = [shape]
        else:
            new_fig2['layout']['shapes'] = []
    else:
        new_fig2['layout']['shapes'] = []
    return new_fig2

@app.callback(
    Output('graph-1', 'figure'),
    [Input('graph-1', 'relayoutData')])
def draw_undecimated_data(selection):
    new_fig1 = fig1.copy()
    if selection is not None and 'xaxis.range[0]' in selection and \
                                 'xaxis.range[1]' in selection:
        x0 = selection['xaxis.range[0]']
        x1 = selection['xaxis.range[1]']
        sub_df = df[(df.Time >= x0) & (df.Time <= x1)]
        num_pts = len(sub_df)
        if num_pts < max_points:
            high_res_data = [
                dict(
                   x=sub_df['Time'],
                   y=sub_df['Signal'],
                   type='scattergl',
                   marker=dict(
                      sizemin=1,
                      sizemax=30,
                      color='darkblue'
                   )
                )]
            high_res_layout = new_fig1['layout']
            high_res = dict( data = high_res_data, layout = high_res_layout)
        else:
            high_res = fig1.copy()
    else:
        high_res = fig1.copy()
    return high_res

app.css.append_css(
    {"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"}
)

if __name__ == '__main__':
    app.run_server(debug=True)
