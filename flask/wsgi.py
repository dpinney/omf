#!/usr/bin/env python


import time
import sys
import os
import json
from flask import Flask, Request, Response, render_template, url_for

import models
import treeParser as tp
import treeGrapher as tg

class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the 
    front-end server to add these headers, to let you quietly bind 
    this to a URL other than / and to an HTTP scheme that is 
    different than what is used locally.

    In nginx:
    location /myprefix {
        proxy_pass http://192.168.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Script-Name /myprefix;
        }

    :param app: the WSGI application
    '''
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

application = app = Flask('wsgi')
app.wsgi_app = ReverseProxied(app.wsgi_app)

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
