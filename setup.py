"""
omf
-----

omf, the Open Modeling Framework, is a set of Python libraries for simulating 
the elctrical grid with an emphasis on cost-benefit analysis of emerging technologies: 
distributed generation, storage, networked controls, etc.

Included is a web interface. For NRECA members, access to a production system is
 available at https://www.omf.coop.

Full documentation is available on our OMF wiki: http://github.com/dpinney/omf/wiki/
"""

from distutils.core import setup

setup(
	name='omf',
	version='0.1',
	url='http://github.com/dpinney/omf/',
	license='TBD',
	author='David Pinney',
	author_email='david.pinney@nreca.coop',
	description='An Open Modeling Framework (omf) for power systems simulation.',
	long_description=__doc__,
	packages=['omf'],
	include_package_data=True, #HUH?
	zip_safe=False, #HUH?
	platforms='any',
	install_requires=open("requirements.txt").readlines(),
	classifiers=[
		'Development Status :: 4 - Beta',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'License :: TBD', # HUH?
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.7',
		'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
		'Topic :: Software Development :: Libraries :: Python Modules']) # HUH?