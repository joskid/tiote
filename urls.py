from django.conf.urls.defaults import patterns, include, url
import settings

urlpatterns = patterns('',
    (r'^$', 'tiote.views.empty'),
    (r'^ajax/$', 'tiote.views.ajax'),
    (r'^bootstrap/$','tiote.views_hm.ender'),
    (r'^login/$', 'tiote.views.login'),
)

