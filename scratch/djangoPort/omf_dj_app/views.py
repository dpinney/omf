# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from models import *
import json

import analysis, feeder, reports, studies, storage, work

def root(request):
	fields = {"feeders":Feeder.objects.all(),
			  "metadatas":Analysis.objects.all()}
	return TemplateResponse(request, "home.html", fields)


def feeder(request, owner, feederName):
	# return HttpResponse(json.dumps(json.loads(User.objects.get(username=owner).feeder_set.get(name=feederName).json)), mimetype="application/json")
	return TemplateResponse(request, "gridEdit.html", {"feederName":feederName,
													   "ref":request.META["HTTP_REFERER"],
													   "owner":owner,
													   "is_admin":True,
													   "anaFeeder":False,
													   "public":True})
	
	
def viewReports(request, owner, analysisName):
	theAnalysis = Analysis.objects.get(name=analysisName)
	thisAnalysis = analysis.Analysis(json.loads(theAnalysis.json))
	studyList = []
	for studyName in thisAnalysis.studyNames:
		studyData = json.loads(theAnalysis.study_set.get(name=studyName).json)
		studyData['name'] = studyName
		studyData['analysisName'] = thisAnalysis.name
		moduleRef = getattr(studies, studyData['studyType'])
		classRef =  getattr(moduleRef, studyData['studyType'].capitalize())
		studyList.append(classRef(studyData))
	reportList = thisAnalysis.generateReportHtml(studyList)
	return TemplateResponse(request, "viewReports.html", {"analysisName":analysisName,
														  "reportList":reportList,
														  "public":True})
def getComponents(request):
	components = {c.name:c.json for c in Component.objects.all()}
	return HttpResponse(json.dumps(components), mimetype="application/json")

def feederData(request, anaFeeder, owner, feederName):
	print feederName
	feeder = Feeder.objects.get(name=feederName, owner=User.objects.get(username=owner))
	return HttpResponse(feeder.json, mimetype="application/json")
