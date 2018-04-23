# There's a full version of this earlier in the repo than 2018-04-20.

@app.before_request
def csrf_protect():
	if request.user_agent.browser == "msie":
		pass
	elif request.user_agent.browser == "firefox":
		pass
	elif request.user_agent.browser != "chrome":
		return "<img style='width:400px;margin-right:auto; margin-left:auto;display:block;' \
			src='http://goo.gl/1GvUMA'><br> \
			<h2 style='text-align:center'>The OMF currently must be accessed by <a href='http://goo.gl/X2ZGhb''>Chrome</a></h2>"
	if request.method == "POST":
	    token = session.pop('_csrf_token', None)
	    if not token or token != request.form.get('_csrf_token'):
	    	if token != request.form.get('csrfToken'):
				abort(403)

def generate_csrf_token():
	if "_csrf_token" not in session:
		session["_csrf_token"] = cryptoRandomString()
	return session["_csrf_token"]

app.jinja_env.globals["csrf_token"] = generate_csrf_token