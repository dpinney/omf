import omf, os, web

if __name__ == "__main__":
	template_files = ["templates/"+ x  for x in web.safeListdir("templates")]
	model_files = ["models/" + x for x in web.safeListdir("models")]
	# Add a sigh route.
	def sigh():
		return 'SIGGGGGGGH'
	web.app.sigh = sigh
	web.app.add_url_rule('/sigh', 'sigh', view_func=web.app.sigh)
	# Start the server.
	web.app.run(
		host='0.0.0.0',
		port=6000,
		threaded=True,
		extra_files=template_files + model_files
	)