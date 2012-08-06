#!/usr/bin/env python


import time
import sys
import os
import json
from flask import Flask, Request, Response, render_template, url_for

import models

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

@app.route('/api/models/<int:model_id>.json')
def api_model(model_id):
	return render_template('default_model.json')

@app.route('/api/objects')
def api_objects():
    all_types = filter(lambda x: x[0] is not '_', dir(models))
    return json.dumps(all_types)

if __name__ == '__main__':
    app.run(debug=True)
