======================================
Django Database Management Application
======================================
Tiote enables django websites to administer PostgreSQL and MySQL databases.

Requirements
=============
sqlalchemy >= 0.6.8
django >= 1.3 
python-psycopg2 ( enables support for PostgreSQL databases)
python-mysqldb ( enables support for MySQL databases)
static-files app for Django versions less than 1.3

Installation
============
In the ``settings.py`` of your django project add 'tiote' to the ``INSTALLED_APPS`` settings.
and run 

		python manage.py syncdb

In the ``urls.py`` of your project add the following entry to the url_patterns

		(r'^tiote/', include('tiote.urls')),

Open link ``<your_project>/tiote`` to begin using tiote. Where ``<your_project>`` is the top level of your django project.



