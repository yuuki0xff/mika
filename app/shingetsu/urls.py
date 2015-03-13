from django.conf.urls import patterns, include, url

_node = '(?P<node>.+)'
_file = '(?P<file>[^/]+)'
_time = '(?P<time>.*)'

urlpatterns = patterns('shingetsu.views',
	url(r'^ping$', 'ping'),
	url(r'^node$', 'node'),
	url(r'^join/'+_node+'$', 'join'),
	url(r'^bye/'+_node+'$', 'bye'),
	url(r'^have/'+_file+'$', 'have'),
	url(r'^get/'+_file+'/'+_time+'$', 'get'),
	url(r'^head/'+_file+'/'+_time+'$', 'head'),
	url(r'^update/'+_file+'/'+_time+'$', 'update'),
	url(r'^recent/'+_time+'$', 'recent'),
)

