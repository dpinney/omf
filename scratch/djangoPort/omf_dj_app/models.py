from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import boto.ses
import hashlib
import random
import time
import json

# Create your models here.

class Feeder(models.Model):
	owner = models.ForeignKey(User)
	name = models.CharField(max_length=200)
	json = models.TextField()

	def __unicode__(self):
		return self.name
	

class Analysis(models.Model):
	owner = models.ForeignKey(User)
	status = models.CharField(max_length=200)
	climate = models.CharField(max_length=200)
	name = models.CharField(max_length=200)
	simStartDate = models.DateField()

	sim_unit_choices = (("minutes", "Minutes"), ("hours", "Hours"), ("days", "Days"))
	simLengthUnits = models.CharField(max_length=10, choices=sim_unit_choices)

	created = models.DateTimeField()

	sourceFeeder = models.ManyToManyField(Feeder)
	simLength = models.IntegerField()
	reports = models.TextField() # json list
	runTime = models.CharField(max_length=200)

	json = models.TextField()
	
	def __unicode__(self):
		return self.name
	
class Study(models.Model):
	analysis = models.ForeignKey(Analysis)
	name = models.CharField(max_length=200)
	json = models.TextField()

	def __unicode__(self):
		return self.analysis.name + "---" + self.name

class Component(models.Model):
	name = models.CharField(max_length=200)
	json = models.TextField()

	def __unicode__(self):
		return self.name

# @receiver(post_save)
def send_reg_email(sender, instance, created, raw, using, update_fields, **kwargs):
	if not created or sender is not User:
		return
	user = instance
	email = user.username
	URL = "localhost:8000"
	message = "Click the link below to register your account for the OMF.  This link will expire in 24 hours:\nreg_link"
	c = boto.ses.connect_to_region("us-east-1",
								   aws_access_key_id="AKIAIFNNIT7VXOXVFPIQ",
								   aws_secret_access_key="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")
	reg_key = hashlib.md5(str(time.time())+str(random.random())).hexdigest()
	outDict = c.send_email("david.pinney@nreca.coop",
						   "OMF Registration Link",
						   message.replace("reg_link", "http://"+URL+"/register/"+email+"/"+reg_key),	
						   [email])
	json.dump(outDict,open(user.username+".json", "w"))
	return
