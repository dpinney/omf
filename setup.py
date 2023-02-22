"""
omf
-----

OMF, the Open Modeling Framework, is a set of Python libraries for simulating 
the elctrical grid with an emphasis on cost-benefit analysis of emerging technologies: 
distributed generation, storage, networked controls, etc. A web interface is included.

Full documentation is available on our OMF wiki: http://github.com/dpinney/omf/wiki/
"""

from distutils.core import setup
import os

#HACK: keep matplotlib from breaking out of sandboxes on Windows.
os.environ["MPLCONFIGDIR"] = "."

setup(
	name = 'omf',
	version = '1.0.0',
	description = 'An Open Modeling Framework (omf) for power systems simulation.',
	long_description = __doc__,
	author = 'David Pinney',
	author_email = 'david.pinney@nreca.coop',	
	url = 'http://github.com/dpinney/omf/',
	packages = ['omf'],
	include_package_data=True,
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'License :: GPLv2',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 3.6',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
		'Topic :: Software Development :: Libraries :: Python Modules'],
	license = 'GPLv2',
	platforms = 'any',
	zip_safe = False, 
	install_requires = [x for x in open("requirements.txt").readlines() if not x.startswith('#')],
)