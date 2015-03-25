from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from lib.models import *
from lib.utils import *
from sqlalchemy.sql import func as sql_func
from binascii import *

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
	def get(self, request, *args, **kwargs):
		s = Session()
		records = []
		limit = int(request.GET.get('limit', -1))

		thread_id = int(kwargs['thread_id'])
		if 'timestamp' in kwargs:
			""" 単一のレコードを返す方のAPI """
			timestamp = int(kwargs['timestamp'])
			bin_id = a2b_hex(kwargs['record_id'])

			r = Record.get(s, thread_id, bin_id, timestamp).with_entities(
					Record.bin_id,
					Record.timestamp,
					Record.name,
					Record.mail,
					Record.body,
					sql_func.length(Record.attach).label('attach_len')).first()
			if r:
				records.append({
					'id': b2a_hex(r.bin_id).decode('ascii'),
					'timestamp': int(datetime2timestamp(r.timestamp)),
					'name': r.name,
					'mail': r.mail,
					'body': r.body,
					'attach': bool(r.attach_len),
					})
		else:
			""" 複数のレコードを返す方のAPI """
			stime = etime = bin_id = None
			if 'start_time' in request.GET:  stime = int(request.GET.get('start_time'))
			if 'end_time' in request.GET:  etime = int(request.GET.get('end_time'))
			if 'id' in request.GET:  bin_id = a2b_hex(kwargs['record_id'])

			matchRecords = Record.gets(s, thread_id, stime, etime, bin_id).with_entities(
					Record.bin_id,
					Record.timestamp,
					Record.name,
					Record.mail,
					Record.body,
					sql_func.length(Record.attach).label('attach_len'))
			for r in matchRecords:
				records.append({
					'id': b2a_hex(r.bin_id).decode('ascii'),
					'timestamp': int(datetime2timestamp(r.timestamp)),
					'name': r.name,
					'mail': r.mail,
					'body': r.body,
					'attach': bool(r.attach_len),
					})
		obj = {
				'records': records,
				}
		return JsonResponse(obj)
	def head(self, request, *args, **kwargs):
		s = Session()
		try:
			thread_id = int(kwargs['thread_id'])
			bin_id = a2b_hex(kwargs['record_id'])
			timestamp = int(kwargs['timestamp'])
		except KeyError:
			return HttpResponseBadRequest()
		if Record.get(s, thread_id, bin_id, timestamp).with_entities(Record.bin_id).first():
			return HttpResponse()
		return HttpResponseNotFound()

class attach(View):
	def get(self, request, *args, **kwargs):
		s = Session()
		try:
			thread_id = int(kwargs['thread_id'])
			bin_id = a2b_hex(kwargs['record_id'])
			timestamp = int(kwargs['timestamp'])
		except KeyError:
			return HttpResponseBadRequest()
		attach = Record.get(s, thread_id, bin_id, timestamp).with_entities(Record.attach).first().attach
		if attach:
			return HttpResponse(attach)
		return HttpResponseNotFound()
	def head(self, request, *args, **kwargs):
		s = Session()
		try:
			thread_id = int(kwargs['thread_id'])
			bin_id = a2b_hex(kwargs['record_id'])
			timestamp = int(kwargs['timestamp'])
		except KeyError:
			return HttpResponseBadRequest()
		if Record.get(s, thread_id, bin_id, timestamp).filter(
				Record.attach is not None
				).first().bin_id:
			return HttpResponse()
		return HttpResponseNotFound(l )


