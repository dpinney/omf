import os.path
from flask import Flask, send_file

app = Flask(__name__)

#Use output from rasterTilesFromOmd function to tiles folder

@app.route('/tiles/<zoom>/<y>/<x>', methods=['GET', 'POST'])
def tiles(zoom, y, x):
    filename = 'tiles/%s/%s/%s.png' % (zoom, x, y)
    default = 'tiles/default.png'
    if os.path.isfile(filename):
        return send_file(filename)
    else:
        return send_file(default)

@app.route('/', methods=['GET', 'POST'])
def index():
    return send_file('tiledMap.html')

if __name__ == '__main__':
    app.run(debug=True)