============
Installation
============
Installation steps can be summarised as making tiote and its associated static fles accessbile by your django project

Requirements
============

Please make sure the following requirements as highlighted below has being met

* sqlalchemy >= 0.6.8
* django >= 1.3
* python-psycopg2 ( enables support for PostgreSQL databases)
* python-mysqldb ( enables support for MySQL databases)
* static-files app for Django versions less than 1.3
* django session app
* Enabled javascript and Cookies in your browser (if not already enabled)


Installation Methods
====================

using pypi
----------

Install from pypi with the handle ``tiote``. i.e.:: 

		pip install tiote

checkout repository
-------------------

Grab a copy of this repository::

		git clone git://github.com/dumb906/tiote 

Switch your directory into the root folder of the directory and run::

		python setup.py install

This makes tiote accessible globally on your python path. 

manual setup
------------
You can also just make the ``tiote`` folder from the project repository be accessible by django's ``manage.py``

Configuration
=============

In the ``settings.py`` of your django project add 'tiote' to the ``INSTALLED_APPS`` settings and ``django.contrib.sessions`` if it is not already there.
and run::

	python manage.py syncdb

.. note::

	If you are running tiote outside the django's development server. You need to setup serving of static files. See `managing static files`_

In the ``urls.py`` of your project, add a url mapping for the tiote application (any address you want)::

	(r'^<custom_url_map>/', include('tiote.urls')),

Open link ``<your_project>/<custom_url_map>`` to begin using tiote. Where ``<your_project>`` is the top level of your django project and ``<custom_url_map>`` is the url mapping for the application


.. _managing static files: https://docs.djangoproject.com/en/dev/howto/static-files.html
