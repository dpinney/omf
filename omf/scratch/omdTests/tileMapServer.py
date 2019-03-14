import os.path
from os.path import join as pJoin
from flask import Flask, send_file

def serveTiles(pathToTiles):
	app = Flask('tester')
	@app.route('/', methods=['GET', 'POST'])
	def index():
		return send_file('tiledMap.html')
	@app.route('/omfTiles/<zoom>/<x>/<y>', methods=['GET'])
	def tiles(zoom, x, y):
		filename = pJoin(pathToTiles, zoom, x, y + '.png')
		default = pJoin(pathToTiles,'default.png')
		if os.path.isfile(filename):
			return send_file(filename)
		else:
			return send_file(default)
	app.run(debug=True)

if __name__ == '__main__':
	serveTiles('tiles')