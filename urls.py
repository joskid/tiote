from django.conf.urls.defaults import patterns, include, url
import settings

urlpatterns = patterns('',
    (r'^$', 'tiote.views.start.index'),
    (r'^ajax/$', 'tiote.views.start.ajax'),
    (r'^login/$', 'tiote.views.start.login'),
)

