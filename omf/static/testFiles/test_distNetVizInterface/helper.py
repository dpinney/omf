import pathlib
import omf


def load_test_files(file_names):
	'''Load the JavaScript unit-test files into a string and return the string'''
	with open(pathlib.Path(omf.omfDir) / 'static' / 'testFiles' / 'test_distNetVizInterface' / 'jasmine-3.5.0' / 'scriptTags.html') as f:
		jasmine = f.read()
	spec = ''
	for name in file_names:
		with open(pathlib.Path(omf.omfDir) / 'static' / 'testFiles' / 'test_distNetVizInterface' / name) as f:
			spec += f.read()
	return {'jasmine': jasmine, 'spec': spec}
