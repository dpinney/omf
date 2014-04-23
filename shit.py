# M-x flask-app

from flask import *

app = Flask(__name__)

def dicks(what):
	return " ".join(map(flask.request.args.get, what))

@app.route("/")
def shit():
	return dicks(["shangus", "crangus"])

if __name__ == "__main__":
	app.run(debug=True)
