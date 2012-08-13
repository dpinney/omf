#!/usr/bin/env python


import time
import sys
import os
import json
from flask import Flask, Request, Response, render_template, url_for

import models
import treeParser as tp
import treeGrapher as tg

application = app = Flask('wsgi')
if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/': os.path.join(os.path.dirname(__file__), 'static')
    })

@app.route('/')
def root():
    return render_template('index.html', model_id='medium')

templates = {
    'house': 
        {
        'name':"new house"
        ,'floor_area':0.0
        ,'schedule_skew':0.0
        ,'heating_system_type':""
        ,'cooling_system_type':""
        ,'cooling_setpoint':""
        ,'heating_setpoint':""
        ,'thermal_integrity_level':""
        ,'air_temperature':0.0
        ,'mass_temperature':0.0
        ,'cooling_COP':0.0
        ,'zip_load':""
        ,'water_heater':""
        },
    'default':
        {
        }
    }

@app.route('/api/modeltemplates/<template_id>')
def api_modeltemplate(template_id):
    if template_id.lowercase() == 'house':
        template = templates['house']
        return json.dumps(template)
    return ""

@app.route("/api/modeltemplates/<type>.html")
def api_new_obj_html(type):
    if type is 'default':
        return render_template('model_modal.html', type=None, props=None)
    else:
        props = templates[type]
        return render_template('model_modal.html', type=type, props=props)

@app.route('/model/<model_id>')
def show_model(model_id):
    return render_template('index.html', model_id=model_id)

@app.route('/api/models/<model_id>/objects/<obj_id>.json')
def api_object(model_id, obj_id):
    return ""

@app.route('/api/models/<model_id>.json')
def api_model(model_id):
    #check file system
    #or, check for GLM file
    if model_id+'.json' in os.listdir('./files/json'):
        in_file = file('./files/json/' + model_id + ".json", "r")
        as_json = in_file.read()
        return as_json
    elif model_id+'.glm' in os.listdir('./files/glms'):
        parsed = tp.parse('./files/glms/' + model_id + ".glm")
        graph = tg.node_groups(parsed)
        # cache the file for later
        out = file('./files/json/' + model_id + ".json", "w")
        graph_json = tg.to_d3_json(graph)
        as_json = json.dumps(graph_json)
        out.write(as_json)
        out.close()
        return as_json
    return ''
	# return render_template('default_model.json')

@app.route('/api/objects')
def api_objects():
    all_types = filter(lambda x: x[0] is not '_', dir(models))
    # all_types = ['House', 'Triplex Meter', 'Meter', 'Node', 'Load']
    return json.dumps(all_types)
    # defaults = map(lambda x: getattr(models, x)().__dict__, all_types)
    # print defaults
    # return json.dumps(defaults)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
