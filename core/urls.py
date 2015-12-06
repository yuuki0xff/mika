from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mika.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

#     url(r'^admin/', include(admin.site.urls)),
	url(r'^server_api/', include('app.shingetsu.urls')),
	url(r'^api/', include('app.rest_api.urls')),
)

