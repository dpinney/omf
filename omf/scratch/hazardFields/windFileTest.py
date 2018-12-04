import matplotlib.pyplot as plt
import numpy as np
import re

def parseHazardFile(inPath):
	with open(inPath, "r") as hazardFile:
		content = hazardFile.readlines()
	content = [x.strip() for x in content]
	hazardObj = {}
	field = []
	for i in range(len(content)):
		if i <= 5:
			line = re.split(r"\s*",content[i])
			hazardObj[line[0]] = line[1] 
		if i > 5:
			field.insert((i-6),map(float,content[i].split(" ")))
	field = np.array(field)
	hazardObj["field"] = field
	return hazardObj

def exportHazardObj(hazardObj, outPath):
	ncols = "ncols        " + hazardObj["ncols"] + "\n"
	nrows = "nrows        " + hazardObj["nrows"] + "\n"
	xllcorner = "xllcorner    " + str(hazardObj["xllcorner"]) + "\n"
	yllcorner = "yllcorner    " + str(hazardObj["yllcorner"]) + "\n"
	cellsize = "cellsize     " + str(hazardObj["cellsize"]) + "\n"
	NODATA_value = "NODATA_value " + hazardObj["NODATA_value"] + "\n"
	output = ncols + nrows + xllcorner + yllcorner + cellsize + NODATA_value
	fieldList = hazardObj["field"].tolist()
	for i in range(len(fieldList)):
		output = output + " ".join(map(str, fieldList[i])) + "\n"
	with open(outPath, "w") as newHazardFile:
		newHazardFile.write("%s" % output)

def moveLocation(x, y, hazardObj):
	hazardObj["xllcorner"] = x
	hazardObj["yllcorner"] = y

def changeCellSize(cellSize, hazardObj): 
	hazardObj["cellsize"] = cellSize

def drawHeatMap(hazardFile):
	heatMap = plt.imshow(hazardFile['field'], cmap='hot', interpolation='nearest')
	plt.gca().invert_yaxis()
	plt.colorbar(heatMap)
	plt.title("Hazard Field")
	plt.show()

def scaleField(scaleFactor, hazardFile):
	for a in np.nditer(hazardFile, op_flags=['readwrite']):
		a[...] = scaleFactor * a

def randomField():
	''' '''
	pass #TODO: implement.

if __name__ == '__main__':
	hazardObj = parseHazardFile("wf_clip.asc")
	# print field
	scaleField(.5, hazardObj["field"])
	moveLocation(20,100, hazardObj)
	changeCellSize(0.5, hazardObj)
	exportHazardObj(hazardObj, "modWindFile.asc")
	hazardObj = parseHazardFile("wf_clip.asc")
	drawHeatMap(hazardObj)