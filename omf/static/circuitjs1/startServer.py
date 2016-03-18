#!/usr/bin/env python
# Script to start a web server for easier circuitjs1 testing.

import SimpleHTTPServer
import SocketServer
import webbrowser

PORT = 8000

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

Handler.extensions_map.update({
    '.webapp': 'application/x-web-app-manifest+json',
});

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "Serving at port", PORT
webbrowser.open_new('http://localhost:8000')
httpd.serve_forever()

