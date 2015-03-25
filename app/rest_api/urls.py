from django.conf.urls import patterns, include, url
from rest_api import views

urlpatterns = patterns('',
	url(r'^versions$', views.versions.as_view() ),
)
