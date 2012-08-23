#!/usr/bin/env python

class GridComponent:
	component = None
	name = None

	def __init__(self, componentDict, name):
		self.component = componentDict
		self.name = name

