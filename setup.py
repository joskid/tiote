#!/usr/bin/env python
import os
from setuptools import setup, find_packages


setup(
	name = 'tiote',
	version = '0.2',
	description = 'Django database administrator',
	author = 'dumb906',
	author_email = 'dumb906@gmail.com',
	url = "https://github.com/dumb906/tiote",
	download_url = "https://github.com/dumb906/tiote/tarball/0.2",
	keywords = ["database", "CRUD", "data"], 
	packages = find_packages(),
	package_data = {'tiote': [
		'static/*/*.*',
		'templates/*.*',
		'templates/*/*.*'
	]},
	classifiers = [
		"Programming Language :: Python",
		"Development Status :: 4 - Beta",
		"License :: OSI Approved :: MIT License",
		"Framework :: Django",
		"Operating System :: OS Independent",
		"Topic :: Database",
		"Topic :: Database :: Front-Ends",
	], 
	long_description = """\
Tiote enables django websites to administer PostgreSQL and MySQL databases.
"""
)