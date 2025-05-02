"""
omf
-----

OMF, the Open Modeling Framework, is a set of Python libraries for simulating 
the elctrical grid with an emphasis on cost-benefit analysis of emerging technologies: 
distributed generation, storage, networked controls, etc. A web interface is included.

Full documentation is available on our OMF wiki: http://github.com/dpinney/omf/wiki/
"""

from pathlib import Path
from setuptools import setup, find_packages
import os

#HACK: keep matplotlib from breaking out of sandboxes on Windows.
os.environ["MPLCONFIGDIR"] = "."

HERE = Path(__file__).parent

long_description = (HERE / "readme.md").read_text(encoding="utf-8")

install_reqs = (HERE / 'requirements.txt').read_text().splitlines()
install_reqs = [r.strip() for r in install_reqs if r and not r.startswith('#')]

setup(
	name = 'omf',
	version = '1.0.0',
	description = 'An Open Modeling Framework (omf) for power systems simulation.',
	long_description = long_description,
    long_description_content_type='text/markdown',
	author = 'David Pinney',
	author_email = 'david.pinney@nreca.coop',	
	url = 'http://github.com/dpinney/omf/',
	# packages = ['omf'],
    packages=find_packages(exclude=['tests*', 'docs*']),
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
    install_requires = install_reqs
)