#!/usr/bin/env python

''' We're gonna render a template from a file. Woohoo! '''

from jinja2 import Template

with open('jinjaTemplatetest.html') as tempFile:
	tempData = tempFile.read()

temp = Template(tempData)
itemList = ['shirt','pants','pantsuit','tracksuit']
outString = temp.render(tempWord='FROMCODE', itemList=itemList)

print outString