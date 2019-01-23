import omf, os, web, logging
from subprocess import Popen

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
	logging.basicConfig(filename='omf.log', level=logging.INFO)
	# Start redirector:
	redirProc = Popen(['gunicorn', '-w', '5', '-b', '0.0.0.0:80', 'webProd:reApp'])
	# Start application:
	appProc = Popen(['gunicorn', '-w', '5', '-b', '0.0.0.0:443', '--certfile=omfDevCert.pem', '--keyfile=omfDevKey.pem', '--preload', 'web:app','--log-file','omf.error.log','--capture-output'])