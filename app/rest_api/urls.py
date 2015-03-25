from django.conf.urls import patterns, include, url
from rest_api import views

urlpatterns = patterns('',
	url(r'^versions$', views.versions.as_view() ),
	url(r'^v0.1/', include('rest_api.v0_1.urls')),
)
