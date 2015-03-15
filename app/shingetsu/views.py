from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
# from shingetsu.models import *
from lib.models import *
from binascii import *
from base64 import b64encode, b64decode
import time
from datetime import datetime

__all__ = 'ping node join bye have get head update recent'.split()

def splitFileName(fname):
	return fname.split('_', 2)

def getRecords(title, stime=None, etime=None):
	s = Session()
	thread_id = s.query(Thread.id).filter(Thread.title == title).first()[0]
	if not thread_id:
		return None
	allRecords = s.query(Record).filter(Record.thread_id == thread_id)
	if stime:
		allRecords = allRecords.filter(Record.timestamp >= stime)
	if etime:
		allRecords = allRecords.filter(Record.timestamp <= etime)
	return allRecords

def record2str(query, include_body=1):
	s = Session()
	if not include_body:
		query = query.with_entities(Record.bin_id, Record.timestamp)
	for r in query:
		line = {}
		if include_body:
			if r.is_post:
				rp = s.query(RecordPost).filter(RecordPost.record_id == r.id).one()
				line['name'] = rp.name
				line['mail'] = rp.mail
				line['body'] = rp.body
			if r.is_remove_notify:
				rr = s.query(RecordRemoveNotify).filter(RecordRemoveNotify.record_id == r.id).one()
				line['remove_id'] = rr.remove_id
				line['remove_stamp'] = rr.remove_stamp
			if r.is_attach:
				ra = s.query(RecordAttach).filter(RecordAttach.record_id == r.id).one()
				line['attach'] = ra.attach #b64encode(ra.attach)
				line['suffix'] = ra.suffix
		yield '{}<>thread<>{}\n'.format(
				int(time.mktime(r.timestamp.timetuple())),
				'<>'.join([key + ':' + str(line[key]) for key in line.keys()]),
			)

def getTimeRange(atime, starttime, endtime):
	if atime:
		return (int(atime), int(atime))
	if starttime:
		if endtime:
			return (int(starttime), int(endtime))
		now = time.mktime(datetime.now().timetuple())
		return (int(starttime), now)
	else:
		if endtime:
			return (0, int(endtime))
		raise 'ERROR'


class ping(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		response.write("PONG\n"+str(addr))
		s = Session()
		if not s.query(Node).filter(Node.host == addr).first():
			s.add(Node(host=addr))
			s.commit()
		s.close()
		return response

class node(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		s = Session()
		nodeAddr = s.query(Node.host).filter(Node.host != addr).value(Node.host)
		if nodeAddr is not None:
			response.write(str(nodeAddr))
		return response

class join(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		if kwargs['node']:
			addr = kwargs['node']
		response = HttpResponse()
		s = Session()
		thisNode = s.query(Node).filter(Node.host == addr).first()
		otherNode = s.query(Node).filter(Node.host != addr).first()
		linkedNodeCount = s.query(Node).filter(Node.linked == True).count()

		welcome = False
		if thisNode:
			welcome = True
			thisNode.linked = True
			s.commit()
		elif linkedNodeCount < 5:
			welcome = True
			s.add(Node(host=addr, linked=True))
			s.commit()

		if welcome:
			response.write('WELCOME')
			if otherNode:
				response.write('\n'+str(otherNode.host))
		return response


class bye(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		if kwargs['node']:
			addr = kwargs['node']
		response = HttpResponse()
		s = Session()
		thisNode = s.query(Node).filter(Node.host == addr).first()
		if thisNode:
			thisNode.linked = False
			s.commit()
			response.write('BYEBYE')
		return response

class have(View):
	def dispatch(self, request, *args, **kwargs):
		prefix, basename = kwargs['file'].split('_')
		response = HttpResponse()
		s = Session()
		if prefix=='thread':
			title = a2b_hex(basename)
			if s.query(Thread.title).filter(Thread.title == title).first():
				response.write('YES')
				return response
		response.write('NO')
		return response

class get(View):
	def dispatch(self, request, *args, **kwargs):
		prefix, basename = splitFileName(kwargs['file'])
		stime, etime = getTimeRange(
				kwargs.get('time'),
				kwargs.get('stime'),
				kwargs.get('etime'),
				)
		response = HttpResponse()
		if prefix=='thread':
			title = a2b_hex(basename)
			allRecords = getRecords(title)
			response.write(''.join(record2str(allRecords)))
		return response

class head(View):
	def dispatch(self, request, *args, **kwargs):
		prefix, basename = splitFileName(kwargs['file'])
		stime, etime = getTimeRange(
				kwargs.get('time'),
				kwargs.get('stime'),
				kwargs.get('etime'),
				)
		response = HttpResponse()
		if prefix=='thread':
			title = a2b_hex(basename)
			allRecords = getRecords(title)
			response.write(''.join(record2str(allRecords, 0)))
		return response

class update(View):
	pass

class recent(View):
	pass
