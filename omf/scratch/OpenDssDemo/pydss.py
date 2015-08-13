
import win32com.client
import os

engine = win32com.client.Dispatch("OpenDSSEngine.DSS")
engine.Start("0")

fname="'Run_ckt5.dss'"
os.chdir('C:\\Users\\mxh7\\OpenDssStuff\\example')
print "We are in ", os.getcwd()
print filter(lambda s: s == "Run_ckt5.dss", os.listdir("."))
engine.Text.Command = "Compile "+fname