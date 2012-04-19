======================================
Django Database Management Application
======================================
Tiote enables django websites to administer PostgreSQL and MySQL databases. It has been tested both on linux (ubuntu), and epio (https://ep.io) environments

Requirements
=============
* sqlalchemy >= 0.6.8
* django >= 1.3
* python-psycopg2 ( enables support for PostgreSQL databases)
* python-mysqldb ( enables support for MySQL databases)
* static-files app for Django versions less than 1.3
* django session app
* Enabled javascript in your browser (if not already enabled)

Installation
============
In the ``settings.py`` of your django project add 'tiote' to the ``INSTALLED_APPS`` settings and ``django.contrib.sessions`` if it is not already there.
and run 

		python manage.py syncdb

In the ``urls.py`` of your project, add a url mapping for the tiote application (any address you want)

		(r'^<custom_url_map>/', include('tiote.urls')),

Open link ``<your_project>/<custom_url_map>`` to begin using tiote. Where ``<your_project>`` is the top level of your django project and ``<custom_url_map>`` is the url mapping for the application

Customization
=============
To have the system catalogs be also displayed as part of the schemas under the Postgresql dialect add the foolowing to your settings.py 

		TT_SHOW_SYSTEM_CATALOGS = True
		
It can be set to True or False