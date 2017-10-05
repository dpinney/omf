import web

if __name__ == "__main__":
	template_files = ["templates/"+ x  for x in web.safeListdir("templates")]
	model_files = ["models/" + x for x in web.safeListdir("models")]
	web.app.run(debug=False, host="0.0.0.0", port=80, extra_files=template_files + model_files)