
from django.views.generic import View
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from lib.models import Session, Thread, Record, Recent, MessageQueue
from lib.utils import datetime2timestamp
from lib.msgqueue import notify
from app.shingetsu.error import BadRecordException
from sqlalchemy.sql import func as sql_func
from binascii import a2b_hex, b2a_hex
from app.shingetsu.utils import makeRecordStr, str2recordInfo
from app.shingetsu import msgqueue
import time

class threads(View):
	def get(self, request, *args, **kwargs):
		threads = []
		gets_kwargs = {}
		if 'limit' in request.GET:
			gets_kwargs['limit'] = int(request.GET.get('limit', -1))
		if 'start_time' in request.GET:
			gets_kwargs['stime'] = int(request.GET.get('start_time'))
		if 'end_time' in request.GET:
			gets_kwargs['etime'] = int(request.GET.get('end_time'))
		if 'title' in request.GET:
			gets_kwargs['title'] = request.GET.get('title')

		with Session() as s:
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
		gets_kwargs = {}
		if 'title' in request.GET:
			gets_kwargs['title'] = request.GET.get('title')

		with Session() as s:
			for t in Thread.gets(s, **gets_kwargs):
				if t.records >=1:
					return HttpResponse()
				break
		return HttpResponseNotFound()
	def post(self, request, *args, **kwargs):
		title = request.POST['title']
		with Session() as s:
			query = Thread.get(s, title=title).all()
			if len(query) == 0:
				thread = Thread.add(s, title)
				MessageQueue.enqueue(s, msgtype='get_thread', msg=Thread.getFileName(title))
				s.commit()
				notify()
			else:
				thread = query[0]
			return JsonResponse({
				'thread': {
					"id": thread.id,
					"title": thread.title,
					"timestamp": thread.timestamp,
					"records": thread.records,
					}
				})

class records(View):
	def get(self, request, *args, **kwargs):
		records = []

		thread_id = int(kwargs['thread_id'])
		with Session() as s:
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
		try:
			thread_id = int(kwargs['thread_id'])
			bin_id = a2b_hex(kwargs['record_id'])
			timestamp = int(kwargs['timestamp'])
		except KeyError:
			return HttpResponseBadRequest()
		with Session() as s:
			if Record.get(s, thread_id, bin_id, timestamp).with_entities(Record.bin_id).first():
				return HttpResponse()
		return HttpResponseNotFound()
	def post(self, request, *args, **kwargs):
		try:
			thread_id = int(kwargs['thread_id'])
			name = request.POST['name']
			mail = request.POST['mail']
			body = request.POST['body']
			try:
				attach = request.POST['attach']
				attach_sfx = request.POST['attach_sfx']
			except KeyError:
				attach = None
				attach_sfx = None
		except KeyError:
			return HttpResponseBadRequest()

		timestamp = time.time()
		try:
			recStr = makeRecordStr(timestamp, name, mail, body, attach, attach_sfx)
		except BadRecordException:
			return HttpResponseBadRequest()
		_, bin_id_hex, body = tuple(str2recordInfo(recStr))[0]
		bin_id = a2b_hex(bin_id_hex)
		with Session() as s:
			Record.add(s, thread_id, timestamp, bin_id, body)
			threadTitle = Thread.get(s, id=thread_id).value(Thread.title)
			Recent.add(s, timestamp, bin_id, Thread.getFileName(threadTitle))
			s.commit()

		msgqueue.updateRecord(thread_id, bin_id_hex, timestamp)
		return HttpResponse()

class attach(View):
	def get(self, request, *args, **kwargs):
		try:
			thread_id = int(kwargs['thread_id'])
			bin_id = a2b_hex(kwargs['record_id'])
			timestamp = int(kwargs['timestamp'])
		except KeyError:
			return HttpResponseBadRequest()
		with Session() as s:
			attach = Record.get(s, thread_id, bin_id, timestamp).with_entities(Record.attach).first().attach
		if attach:
			return HttpResponse(attach)
		return HttpResponseNotFound()
	def head(self, request, *args, **kwargs):
		try:
			thread_id = int(kwargs['thread_id'])
			bin_id = a2b_hex(kwargs['record_id'])
			timestamp = int(kwargs['timestamp'])
		except KeyError:
			return HttpResponseBadRequest()
		with Session() as s:
			if Record.get(s, thread_id, bin_id, timestamp).filter(
					Record.attach is not None
					).first().bin_id:
				return HttpResponse()
		return HttpResponseNotFound()


