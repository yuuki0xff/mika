from django.conf.urls import patterns, include, url
from app.rest_api.v0_1.views import *

_thread_id = '(?P<thread_id>[0-9]+)'
_timestamp = '(?P<timestamp>[0-9]+)'
_record_id = '(?P<record_id>[0-9a-fA-F]+)'

urlpatterns = patterns('',
	url(r'^threads$', threads.as_view()),
	url(r'^records/'+_thread_id+'/'+_timestamp+'/'+_record_id+'$', records.as_view()),
	url(r'^records/'+_thread_id+'$', records.as_view()),
	url(r'^attach/'+_thread_id+'/'+_timestamp+'/'+_record_id+'$', attach.as_view()),
)

