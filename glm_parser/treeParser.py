#!/usr/bin/env python

def tokenizeGlm(glmFileName):
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
    # Tokenize around semicolons, braces and whitespace.
    tokenized = re.split(r'(;|\}|\{|\s)',data)
    # Get rid of whitespace strings.
    basicList = filter(lambda x:x!='' and x!=' ', tokenized)
    return basicList

def parseTokenList(tokenList):
	# Tree variables.
	tree = {}
	guid = 0
	guidStack = []
	# Helper function to add to the current leaf we're visiting.
	def currentLeafAdd(key, value):
		current = tree
		for x in guidStack:
			current = current[x]
		current[key] = value
	# Helper function to turn a list of strings into one string with some decent formatting.
	# TODO: formatting could be nicer, i.e. remove the extra spaces this function puts in.
	def listToString(listIn):
		if len(listIn) == 0:
			return ''
		else:
			return reduce(lambda x,y:str(x)+' '+str(y),listIn[1:-1])
	# Pop off a full token, put it on the tree, rinse, repeat.
	while tokenList != []:
		# Pop, then keep going until we have a full token (i.e. 'object house', not just 'object')
		fullToken = []
		while fullToken == [] or fullToken[-1] not in ['{',';','}']:
			fullToken.append(tokenList.pop(0))
		# Work with what we've collected.
		if fullToken[-1] == ';':
			# Special case when we have zero-attribute items (like #include, #set, module).
			if guidStack == [] and fullToken != [';']:
				tree[guid] = {'omftype':fullToken[0],'argument':listToString(fullToken)}
				guid += 1
			# We process if it isn't the empty token (';')
			elif len(fullToken) > 1:
				currentLeafAdd(fullToken[0],listToString(fullToken))
		elif fullToken[-1] == '}':
			if len(fullToken) > 1:
				currentLeafAdd(fullToken[0],listToString(fullToken))
			guidStack.pop()
		elif fullToken[-1] == '{':
			currentLeafAdd(guid,{})
			guidStack.append(guid)
			guid += 1
			# Wrapping this currentLeafAdd is defensive coding so we don't crash on malformed glms.
			if len(fullToken) > 1:
				# Do we have a clock/object or else an embedded configuration object?
				if len(fullToken) < 4:
					currentLeafAdd(fullToken[0],fullToken[-2])
				else:
					currentLeafAdd('omfEmbeddedConfigObject', fullToken[0] + ' ' + listToString(fullToken))
	return tree

def parse(glmFileName):
	tokens = tokenizeGlm(glmFileName)
	return parseTokenList(tokens)



#Some test code follows:
#tokens = ['clock','{','clockey','valley','}','object','house','{','name','myhouse',';','object','ZIPload','{','inductance','bigind',';','power','newpower','}','size','234sqft','}']
#simpleTokens = tokenizeGlm('testglms/Simple_System.glm')
#print parseTokenList(simpleTokens)
