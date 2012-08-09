#!/usr/bin/env python


import time
import sys
import os
import json
from flask import Flask, Request, Response, render_template, url_for

import models
import treeParser as tp
import treeGrapher as tg
from networkx_ext import d3_js

application = app = Flask('wsgi')
if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    import os
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
      '/': os.path.join(os.path.dirname(__file__), 'static')
    })

@app.route('/')
def root():
    return render_template('index.html')

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
        graph_json = d3_js.d3_json(graph)
        as_json = json.dumps(graph_json)
        out.write(as_json)
        out.close()
        return as_json
    return ''
	# return render_template('default_model.json')

@app.route('/api/objects')
def api_objects():
    all_types = filter(lambda x: x[0] is not '_', dir(models))
    return json.dumps(all_types)
    # defaults = map(lambda x: getattr(models, x)().__dict__, all_types)
    # print defaults
    # return json.dumps(defaults)

if __name__ == '__main__':
    app.run(debug=True)
