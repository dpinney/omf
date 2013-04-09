import os
import studies as sm

analyses = os.listdir('analyses')

for analysis in analyses:
	studies = os.listdir('analyses/' + analysis + '/studies/')
	for study in studies:
		sm.gridlabd.generateReferenceOutput(analysis, 'analyses/' + analysis + '/studies/' + study)
		print study