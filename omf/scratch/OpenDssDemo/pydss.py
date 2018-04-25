import platform
import os

if platform.system()=='Windows':
	# PREREQUISITE: OpenDSS. It's out on the internet somehwere...
	import win32com.client
	engine = win32com.client.Dispatch("OpenDSSEngine.DSS")
	engine.Start("0")
	fname="'Run_ckt5.dss'"
	os.chdir('C:\\Users\\mxh7\\OpenDssStuff\\example')
	print "We are in ", os.getcwd()
	print filter(lambda s: s == "Run_ckt5.dss", os.listdir("."))
	engine.Text.Command = "Compile "+fname
elif platform.system()=='Darwin' or platform.system() == "Linux":
	# PREREQUISITE: pip install 'OpenDSSDirect.py[extras]'
	import opendssdirect as dss
	dss.run_command('Redirect DSSscript.dss')