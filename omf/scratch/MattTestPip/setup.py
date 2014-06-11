
from distutils.core import setup

setup(
	name='MattTestPip',
	version='0.1.1',
	author='Matt Havard',
	author_email='Matthew.Havard@nreca.coop',
	packages=['matttestpip', 'matttestpip.test'],
	url='http://pypi.python.org/pypi/MattTestPip/',
	license='LICENSE.txt',
	description='Testing out pip-packaging',
	long_description=open('README.txt').read(),
	install_requires=[],
	)