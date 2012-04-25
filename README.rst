======================================
Django Database Management Application
======================================
Tiote enables django websites to administer PostgreSQL and MySQL databases. It provides a clean and intuitive interface to your database(s) with which you can use Database level functions. This functions can be summarised as CRUD (Create, Read, Update and Delete). It has been tested both on linux (ubuntu), and epio (https://ep.io) environments.

Requirements
=============
* sqlalchemy >= 0.6.8
* django >= 1.3
* python-psycopg2 ( enables support for PostgreSQL databases)
* python-mysqldb ( enables support for MySQL databases)
* static-files app for Django versions less than 1.3
* django session app
* Enabled javascript and Cookies in your browser (if not already enabled)

Installation
============
Install from pypi with the handle ``tiote``. i.e. ``pip install tiote``

Or you can grab a copy of this repository. Switch your directory into the root folder of the directory and run ``python setup.py install`` for it to be available system wide or just place the tiote folder in a location that can be accessed by your django project. 

Configuration
-------------
In the ``settings.py`` of your django project add 'tiote' to the ``INSTALLED_APPS`` settings and ``django.contrib.sessions`` if it is not already there.
and run 

		python manage.py syncdb

In the ``urls.py`` of your project, add a url mapping for the tiote application (any address you want)

				(r'^<custom_url_map>/', include('tiote.urls')),

Open link ``<your_project>/<custom_url_map>`` to begin using tiote. Where ``<your_project>`` is the top level of your django project and ``<custom_url_map>`` is the url mapping for the application

Customization
=============
All this settings are to be entered in settings.py or its equivalent

* ``TT_SHOW_SYSTEM_CATALOGS`` Include (set to True) or exclude (set to False) system catalogs. Excluding system catalogs is the default and increases individual page load

* ``TT_SESSION_EXPIRY``: accepts an integer (default 1800) which is the amount of seconds before the session expires (to be asked to log on again). It doesn't conflict with other sessions from other django applications.

* ``TT_MAX_ROW_COUNT`` : accepts an integer (defaults to 100 ) which is the amount of rows displayed in any table under 'browse' view of section 'table'

