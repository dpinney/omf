#!/usr/bin/env python
# encoding: utf-8

"""
GLMParserRecursive.py
Created by David Pinney on 2012-05-08.
"""

import sys
import os

def tokenizeGLM(glmFileName):
    import re
    file = open(glmFileName)
    data = file.read()
    
    # Get rid of http for stylesheets because we don't need it and it conflicts with comment syntax.
    data = re.sub(r'http:\/\/', '', data)
    
    # Strip comments.
    data = re.sub(r'\/\/.*\n', '', data)
    
    # TODO: If the .glm creator has been lax with semicolons, add them back.
    
    # Also strip non-single whitespace because it's only for humans:
    data = data.replace('\n','').replace('\r','').replace('\t',' ')
    
    # Tokenize around semicolons and whitespace.
    tokenized = re.split(r'(;|\s)',data)
    
    # Get rid of whitespace strings.
    basicList = filter(lambda x:x!='' and x!=' ', tokenized)
    
    return basicList

def gatherDeepestNest(tokenizedGLM):
    #Helper function: backtrack from an open brace to get all the input stuff.
    def grabHeader(x, tokenizedGLM):
        pointer = x
        while tokenizedGLM[pointer] != ';':
            if pointer == 0: return pointer
            else: pointer += -1
        return pointer + 1
    # Function starts here.
    maxLen = len(tokenizedGLM)
    startRange = None
    accum = []
    for x in xrange(0, maxLen):
        if tokenizedGLM[x] == '{':
            startRange = grabHeader(x, tokenizedGLM)
        if tokenizedGLM[x] == '}' and startRange != None:
            accum += [[startRange, x+2]]
            startRange = None
    return accum

def objectToDict(tokenList):
    stack = list(tokenList)
    bracket = tokenList.index('{')
    head = tokenList[0:bracket]
    tail = tokenList[bracket+1:-2]
    accumDict = {}
    # Process the head.
    if len(head) == 1:
        accumDict['type'] = head[0]
    elif len(head) == 2:
        accumDict['type'] = head[1]
    else:
        accumDict['type'] = head[2]        
    # Process the tail.
    # TODO: enhance this to cover the case where we have already dictified something.
    tailStack = []
    # We need to keep track of how many objects of each type so we don't clobber their keys.
    typeDict = {}
    while len(tail) > 0:
        current = tail.pop(0)
        if type(current) is dict:
            key = current['type']
            # Update our type dictionary.
            if key in typeDict:
                typeDict[key] += 1
                # We've seen this object before, so append a version number to our outKey.
                outKey = key + str(typeDict[key])
            else:
                typeDict[key] = 0
                outKey = key
            # Write out our dictionary.
            accumDict[outKey] = current
        elif current != ';':
            tailStack += [current]
        else:
            accumDict[tailStack.pop(0)] = reduce(lambda x,y:str(x)+' '+str(y), tailStack)
            tailStack = []
    return accumDict

staticToken = tokenizeGLM('testglms/Simple_System.glm')
print staticToken

# TODO: Debug.
def dictifyDeepest(tokenizedGLM):
    outList = list(tokenizedGLM)
    deepCoords = gatherDeepestNest(tokenizedGLM)
    adjustment = 0
    for x in deepCoords:
        start = x[0] - adjustment
        end = x[1] - adjustment
        outList[start] = objectToDict(outList[start:end])
        del outList[start+1:end]
        adjustment += end - start - 1
    return outList

print objectToDict(['object', 'stubauction', '{', 'name', 'Market_1', ';', 'period', '300', ';', {'type': 'player', 'loop': '365', 'file': 'Price.player'}, '}', ';'])

print gatherDeepestNest(staticToken)

firstLevObjects = map(lambda x:objectToDict(staticToken[x[0]:x[1]]),gatherDeepestNest(staticToken))
print map(lambda x:x['type'],firstLevObjects)