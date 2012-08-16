#!/usr/bin/env python

import grid

glmFile = open('neoMain.glm','r')
glmString = glmFile.read()

testGrid = grid.Grid(glmString)

print testGrid.tree