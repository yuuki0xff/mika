
from django.views.generic import View
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from lib.models import Session, Thread, Record, RecordAttach, RecordRaw, Recent, MessageQueue
from lib.utils import datetime2timestamp
from lib.msgqueue import notify
from app.shingetsu.error import BadRecordException
import sqlalchemy.sql as sql
from sqlalchemy.exc import IntegrityError
from binascii import a2b_hex, b2a_hex
from app.shingetsu.utils import makeRecordStr, str2recordInfo
from app.shingetsu import msgqueue
import time

def intOrNone(string):
	if not string:
		return None
	return int(string)

class threads(View):
	def get(self, request, *args, **kwargs):
		threads = []
		with Session() as s:
			result = Thread.gets(s,
					limit=intOrNone(request.GET.get('limit')),
					stime=intOrNone(request.GET.get('start_time')),
					etime=intOrNone(request.GET.get('end_time')),
					title=request.GET.get('title'),
					)
			for t in result:
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
		with Session() as s:
			for t in Thread.gets(s, title=request.GET.get('title')):
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
						Record.suffix).first()
				if r:
					records.append({
						'id': b2a_hex(r.bin_id).decode('ascii'),
						'timestamp': int(datetime2timestamp(r.timestamp)),
						'name': r.name,
						'mail': r.mail,
						'body': r.body,
						'attach': bool(r.suffix),
						'suffix': r.suffix,
						})
			else:
				""" 複数のレコードを返す方のAPI """
				bin_id = request.GET.get('record_id')
				if bin_id:
					bin_id = a2b_hex(bin_id)

				matchRecords = Record.gets(s,
						thread_id=thread_id,
						stime=intOrNone(request.GET.get('start_time')),
						etime=intOrNone(request.GET.get('end_time')),
						bin_id=bin_id,
						limit=intOrNone(request.GET.get('limit')),
					).with_entities(
							Record.bin_id,
							Record.timestamp,
							Record.name,
							Record.mail,
							Record.body,
							Record.suffix)
				for r in matchRecords:
					records.append({
						'id': b2a_hex(r.bin_id).decode('ascii'),
						'timestamp': int(datetime2timestamp(r.timestamp)),
						'name': r.name,
						'mail': r.mail,
						'body': r.body,
						'attach': bool(r.suffix),
						'suffix': r.suffix,
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
			try:
				Record.add(s, thread_id, timestamp, bin_id, body)
				s.commit()
				threadTitle = Thread.get(s, id=thread_id).value(Thread.title)
				Recent.add(s, timestamp, bin_id, Thread.getFileName(threadTitle))
				s.commit()
				msgqueue.updateRecord(thread_id, bin_id_hex, timestamp)
			except IntegrityError:
				s.rollback()
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
			record = Record.get(s, thread_id, bin_id, timestamp).first()
			if not record:
				return HttpResponseNotFound()
			query = sql.select([RecordAttach.attach])\
					.where(sql.and_(*[
						record.thread_id == RecordRaw.thread_id,
						record.timestamp == RecordRaw.timestamp,
						record.bin_id == RecordRaw.bin_id,
					]))
			row = s.execute(query).first()
			if not row:
				return HttpResponseNotFound()
			return HttpResponse(row[0])
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


