from django.conf.urls.defaults import patterns, include, url
import settings

urlpatterns = patterns('',
    (r'^$', 'tiote.views.begin.empty'),
    (r'^ajax/$', 'tiote.views.begin.ajax'),
    (r'^bootstrap/$','tiote.views.begin_hm.ender'),
    (r'^login/$', 'tiote.views.begin.login'),
)

