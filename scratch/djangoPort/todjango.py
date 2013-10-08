import os
import json
from datetime import datetime

os.environ["DJANGO_SETTINGS_MODULE"] = "dj_omf.settings"

from omf_dj_app.models import *

def create_feeders(public):
	for feeder in os.listdir("data/Feeder"):
		if feeder.startswith("public_"):
			name = feeder[len("public_"):-len(".json")]
			if len(Feeder.objects.filter(name=name)) == 0:
				print (Feeder.objects.create(owner=public,
									  name=name,
									  json=json.dumps(json.load(open("data/Feeder/"+feeder)))))

def create_analyses(public):
	for ana in os.listdir("data/Analysis"):
		if ana.startswith("public_z"):
			name = ana[len("public_z"):-len(".json")]
			ana_dict = json.load(open("data/Analysis/"+ana))
			if len(Analysis.objects.filter(name=name)) == 0:
				
				ana_dict["name"] = name
				sourceFeeders = []
				for f in ana_dict["sourceFeeder"].split(", "):
					try:
						sourceFeeders.append(Feeder.objects.get(name=f))
					except Exception:
						print "Feeder", f, "does not exist"
				new_ana = Analysis.objects.create(status=ana_dict["status"],
												  climate=ana_dict["climate"],
												  owner=public,
												  name=name,
												  runTime=ana_dict["runTime"],
												  simStartDate=datetime.strptime(ana_dict["simStartDate"], "%Y-%m-%d"),
												  simLengthUnits=ana_dict["simLengthUnits"],
												  created=datetime.strptime(ana_dict["created"], "%Y-%m-%d %H:%M:%S.%f"),
												  simLength=ana_dict["simLength"],
												  json=json.dumps(ana_dict),
												  reports=json.dumps(ana_dict["reports"]))
				new_ana.sourceFeeder.add(*sourceFeeders)
			else:
				new_ana = Analysis.objects.get(name=name)
			create_studies(new_ana, ana_dict["studyNames"])
				
			print new_ana

def create_studies(ana, studyNames):
	for name in studyNames:
		if len(ana.study_set.filter(name=name)) == 0:
			try:
				print (Study.objects.create(analysis=ana,
											name=name,
											json=open("data/Study/public_z"+ana.name+"---"+name+".json").read()))
			except Exception:
				print "\n+-----------------------------------+"
				print "Study", name, "probably doesn't exist"
				print "+--------------------------------------+\n"

def create_components():
	for c in os.listdir("data/Component"):
		name = c[:-len(".json")]
		if len(Component.objects.filter(name=name)) == 0:
			print (Component.objects.create(name=name, json=json.dumps(json.load(open("data/Component/"+c)))))

if __name__ == "__main__":
	try:
		public = User.objects.get(username="public")
	except Exception:
		public = User.objects.create_user(username="public", email="public@public.com", password="public")
		print "public user created"
	print "CREATING FEEDERS!!!"
	create_feeders(public)
	print "CREATING ANALYSES AND STUDIES"
	create_analyses(public)
	print "CREATING COMPONENTS!!!!"
	create_components()
	print "Done!"
