Customisation
-------------
Tiote comes with some reasonable defaults which take bandwidth and the number of database queries into consideration. But if your needs include more finetuning and plumbling then here are some options with which you can change the default behaviour of tiote.

All this settings are to be entered in settings.py or its equivalent

* ``TT_SHOW_SYSTEM_CATALOGS`` Include (set to True) or exclude (set to False) system catalogs. Excluding system catalogs is the default and increases individual page load. This option is only for the PostgreSQL dialect.

* ``TT_SESSION_EXPIRY``: accepts an integer (default 1800) which is the amount of seconds before the session expires (to be asked to log on again). It doesn't conflict with other sessions from other django applications.

* ``TT_MAX_ROW_COUNT`` : accepts an integer (defaults to 100 ) which is the amount of rows displayed in any table under 'browse' view of section 'table'