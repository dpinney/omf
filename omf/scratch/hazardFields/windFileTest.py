import matplotlib.pyplot as plt
import numpy as np
import re, random



class WindFileObj(object):

	def __init__(self, filePath):
		''' Use parsing function to set up harzard data in dict format in constructor.'''
		self.hazardObj = self.parseHazardFile(filePath)


	def parseHazardFile(self, inPath):
		''' Parse input file. '''
		with open(inPath, "r") as hazardFile: # Parse the file, strip away whitespaces.
			content = hazardFile.readlines()
		content = [x.strip() for x in content]
		hazardObj = {}
		field = []
		for i in range(len(content)): 
			if i <= 5: # First, get the the parameters for the export function below. Each gets their own entry in our object.
				line = re.split(r"\s*",content[i])
				hazardObj[line[0]] = line[1] 
			if i > 5: # Then, get the numerical data, mapping each number to its appropriate parameter.
				field.insert((i-6),map(float,content[i].split(" "))) 
		field = np.array(field)
		hazardObj["field"] = field
		return hazardObj

	def exportHazardObj(self, outPath):
		''' Export file. ''' 
		ncols = "ncols        " + self.hazardObj["ncols"] + "\n" # Get parameters from object.
		nrows = "nrows        " + self.hazardObj["nrows"] + "\n"
		xllcorner = "xllcorner    " + str(self.hazardObj["xllcorner"]) + "\n"
		yllcorner = "yllcorner    " + str(self.hazardObj["yllcorner"]) + "\n"
		cellsize = "cellsize     " + str(self.hazardObj["cellsize"]) + "\n"
		NODATA_value = "NODATA_value " + self.hazardObj["NODATA_value"] + "\n"
		output = ncols + nrows + xllcorner + yllcorner + cellsize + NODATA_value
		fieldList = self.hazardObj["field"].tolist() # Get numerical data, convert each number to a string and add that onto the to-be exported data. 
		for i in range(len(fieldList)):
			output = output + " ".join(map(str, fieldList[i])) + "\n"
		with open(outPath, "w") as newHazardFile: # Export to new file.
			newHazardFile.write("%s" % output)

	def moveLocation(self, x, y): 
		''' Shift temporal boundaries for image plot. ''' 
		self.hazardObj["xllcorner"] = x
		self.hazardObj["yllcorner"] = y

	def changeCellSize(self, cellSize): 
		''' Scale the cell size in image plot. '''
		self.hazardObj["cellsize"] = cellSize

	def drawHeatMap(self):
		''' Draw heat map-color coded image map with user-defined boundaries and cell-size. '''
		heatMap = plt.imshow(self.hazardObj['field'], cmap='hot', interpolation='nearest', extent=[0, self.hazardObj["xllcorner"], 0, self.hazardObj["yllcorner"]], aspect=self.hazardObj["cellsize"])
		#plt.gca().invert_yaxis() This isn't needed anymore?
		plt.colorbar(heatMap)
		plt.title("Hazard Field")
		plt.show()

	def scaleField(self, scaleFactor):
		''' Numerically scale the field with user defined scaling factor. ''' 
		for a in np.nditer(self.hazardObj["field"], op_flags=['readwrite']):
			a[...] = scaleFactor * a

	def randomField(self, lowerLimit = 0, upperLimit = 100):
		''' Generate random field with user defined limits. '''
		for a in np.nditer(self.hazardObj["field"], op_flags=['readwrite']):
			a[...] = random.randint(lowerLimit, upperLimit) 


if __name__ == "__main__":
	windObj = WindFileObj("wf_clip.asc")
	windObj.scaleField(.5)
	windObj.randomField()
	windObj.moveLocation(20, 100)
	windObj.changeCellSize(0.5)
	windObj.exportHazardObj("modWindFile.asc")
	windObj.drawHeatMap()
