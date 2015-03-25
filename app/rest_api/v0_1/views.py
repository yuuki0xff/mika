from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from lib.models import *
from lib.utils import *

class threads(View):
	def get(self, request, *args, **kwargs):
		s = Session()
		threads = []
		gets_kwargs = {}
		if 'limit' in request.GET:  gets_kwargs['limit'] = int(request.GET.get('limit', -1))
		if 'start_time' in request.GET:  gets_kwargs['stime'] = int(request.GET.get('start_time'))
		if 'end_time' in request.GET:  gets_kwargs['etime'] = int(request.GET.get('end_time'))
		if 'title' in request.GET:  gets_kwargs['title'] = request.GET.get('title')

		for t in Thread.gets(s, **gets_kwargs):
			threads.append({
				'id': int(t.id),
				'title': t.title,
				'timestamp': int(datetime2timestamp(t.timestamp)),
				'records': int(t.records),
				})
		obj = {
				'threads': threads
				}
		return JsonResponse(obj)
	def head(self, request, *args, **kwargs):
		s = Session()
		gets_kwargs = {}
		if 'title' in request.GET:  gets_kwargs['title'] = request.GET.get('title')

		for t in Thread.gets(s, **gets_kwargs):
			if t.records >=1:
				return HttpResponse()
			break
		return HttpResponseNotFound()

class records(View):
	pass

class attach(View):
	pass


