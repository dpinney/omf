import json
from omf.models import voltageDrop
from omf import feeder
import anonymization



feeder.glmToOmd('/Users/tuomastalvitie/Desktop/Random_Feeder_files/Chester_Jan2017_fixed.glm', '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Chester_Jan2017_fixed.omd')
feeder.glmToOmd('/Users/tuomastalvitie/Desktop/Random_Feeder_files/Conway_Jan2017_fixed.glm', '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Conway_Jan2017_fixed.omd')
feeder.glmToOmd('/Users/tuomastalvitie/Desktop/Random_Feeder_files/Fairgrounds_Jan2017_fixed.glm', '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Fairgrounds_Jan2017_fixed.omd')
feeder.glmToOmd('/Users/tuomastalvitie/Desktop/Random_Feeder_files/Sunapee_Jan2017_fixed.glm', '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Sunapee_Jan2017_fixed.omd')


chester = '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Chester_Jan2017_fixed.omd'
conway = '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Conway_Jan2017_fixed.omd'
fairgrounds = '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Fairgrounds_Jan2017_fixed.omd'
sunapee = '/Users/tuomastalvitie/Desktop/Random_Feeder_files/Sunapee_Jan2017_fixed.omd'

nameList= [chester, conway, fairgrounds, sunapee]
anonNameList = []

for i in nameList:
	with open(i, "r") as inFile:
			inFeeder = json.load(inFile)
			nameKey = anonymization.distPseudomizeNames(inFeeder)
			anonymization.distRandomizeNames(inFeeder)
			anonymization.distRandomizeLocations(inFeeder)
			translationRight = 20
			translationUp = 20
			rotation = 20
			anonymization.distTranslateLocations(inFeeder, translationRight, translationUp, rotation)
			FNAMEOUT = i.split('.')[0] + '_anonymized.omd'
			anonNameList.append(FNAMEOUT)
	with open(FNAMEOUT, "w") as outFile:
		json.dump(inFeeder, outFile, indent=4)

for i in anonNameList:
	chart = voltageDrop.drawPlot(i, neatoLayout=False, edgeCol="PercentOfRating", nodeCol="perUnitVoltage", nodeLabs="Value", edgeLabs="Name", customColormap=True, rezSqIn=225)
	chart.savefig(i.split('.')[0] + '.png')
	chartFL = voltageDrop.drawPlot(i, neatoLayout=True, edgeCol="PercentOfRating", nodeCol="perUnitVoltage", nodeLabs="Value", edgeLabs="Name", customColormap=True, rezSqIn=225)
	chart.savefig(i.split('.')[0] + "_ForceLayout.png")
