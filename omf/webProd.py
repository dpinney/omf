import omf, os, web, logging
from multiprocessing import Process

# Note: sudo python webProd.py on macOS since this will open low numbered ports.
# If you need some test certs: openssl req -x509 -newkey rsa:4096 -nodes -out omfDevCert.pem -keyout omfDevKey.pem -days 365 -subj '/CN=localhost/O=NoCompany/C=US'

reApp = web.Flask('OMFR')

@reApp.route('/')
def index():
	return 'NA'

@reApp.before_request
def before_request():
	if web.request.url.startswith('http://'):
		url = web.request.url.replace('http://', 'https://', 1)
		code = 301
		return web.redirect(url, code=code)

if __name__ == "__main__":
	logging.basicConfig(filename='omf.log', level=logging.DEBUG)
	template_files = ["templates/"+ x  for x in web.safeListdir("templates")]
	model_files = ["models/" + x for x in web.safeListdir("models")]
	# HTTP redirector:
	reAppKwargs = {
		'host':'0.0.0.0',
		'port':80,
		'threaded':True
	}
	Process(target=reApp.run, kwargs=reAppKwargs).start()
	# HTTPS (main app):
	sslAppKwargs = {
		'host':'0.0.0.0',
		'port':443,
		'threaded':True,
		'extra_files':template_files + model_files,
		'ssl_context':('omfDevCert.pem','omfDevKey.pem')
	}
	Process(target=web.app.run, kwargs=sslAppKwargs).start()