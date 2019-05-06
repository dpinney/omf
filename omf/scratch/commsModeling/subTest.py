import subprocess, webbrowser
from PIL import Image

#Run this to produce png image of RF

sourceQth = [
	"Source Name",
	"36 25 37.49",
	"103 29 06.0",
	"94m"
	]

#write file
with open("signalSource.qth", "w") as sourceFile:
	#name of the antenna
	for i in sourceQth:
		sourceFile.write(i)
		sourceFile.write("\n")

sourceLrp = [
	"15.000 ; Earth Dielectric Constant (Relative permittivity)",
	"0.005 ; Earth Conductivity (Siemens per meter)",
	"301.000 ; Atmospheric Bending Constant (N-units)",
	"474.000 ; Frequency in MHz (20 MHz to 20 GHz)",
	"5 ; Radio Climate (5 = Continental Temperate)",
	"0 ; Polarization (0 = Horizontal, 1 = Vertical)",
	"0.50 ; Fraction of situations (50 % of locations)",
	"0.90 ; Fraction of time (90% of the time)",
	"150000.0 ; Effective Radiated Power (ERP) in Watts (optional)"
	]

with open("signalSource.lrp", "w") as sourceFile:
	for i in sourceLrp:
		sourceFile.write(i)
		sourceFile.write("\n")

args = ["splat", "-t", "tx1.qth", "-c", "10", "-metric", "-o", "out.ppm", "-kml", "-d", "sdf"]

subprocess.Popen(args).wait()

im = Image.open("out.ppm")
im.save("out.png")
webbrowser.open_new('kmlMap.html')