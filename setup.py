"""
omf
-----

OMF, the Open Modeling Framework, is a set of Python libraries for simulating 
the elctrical grid with an emphasis on cost-benefit analysis of emerging technologies: 
distributed generation, storage, networked controls, etc.

Included is a web interface. For NRECA members, access to a production system is
 available at https://www.omf.coop.

Full documentation is available on our OMF wiki: http://github.com/dpinney/omf/wiki/
"""

from distutils.core import setup
from setuptools import find_packages

setup(
	name = 'omf',
	version = '0.2',
	description = 'An Open Modeling Framework (omf) for power systems simulation.',
	long_description = __doc__,
	author = 'David Pinney',
	author_email = 'david.pinney@nreca.coop',
	# maintainer = '',
	# maintainer_email = '',
	url = 'http://github.com/dpinney/omf/',
	# download_url = 'http://github.com/dpinney/omf/',
	packages = find_packages(), # TODO: Fix either project layout or package list.
	# py_modules = ['omf'],
	# scripts = '',
	# ext_modules = '',
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'License :: TBD', # TODO
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.7',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
		'Topic :: Software Development :: Libraries :: Python Modules'],
	# distclass = '',
	# script_name = '',
	# script_args = '',
	# options = '',
	license = 'TBD',
	# keywords = [],
	platforms = 'any',
	# cmdclass = [],
	# data_files = [],
	# package_dir = {},

	## NOTE: the following keywords are from setuptools package.
	# include_package_data = True, #HUH?
	# exclude_package_data = {},
	# package_data = {},
	zip_safe = False, 
	install_requires = open("requirements.txt").readlines(),
	# extras_require = {},
	# setup_requires = [],
	# dependency_links = '',
	# namespace_packages = [],
	# test_suite = '',
	# tests_require = [],
	# test_loader = '',
	# eager_resources = [],
	# use_2to3 = False,
	# convert_2to3_doctests = [],
	# use_2to3_fixers = [],
	) 
