from django.conf.urls import patterns, include, url
from app.shingetsu.views import *

_node = '(?P<node>.+)'
_file = '(?P<file>[^/]+)'
_time = '(?P<time>.*)'

urlpatterns = patterns('',
	url(r'^ping$', ping.as_view()),
	url(r'^node$', node.as_view()),
	url(r'^join/'+_node+'$', join.as_view()),
	url(r'^bye/'+_node+'$',  bye.as_view()),
	url(r'^have/'+_file+'$', have.as_view()),
	url(r'^get/'+_file+'/'+_time+'$', get.as_view()),
	url(r'^head/'+_file+'/'+_time+'$', head.as_view()),
	url(r'^update/'+_file+'/'+_time+'$', update.as_view()),
	url(r'^recent/'+_time+'$', 'recent'),
)

