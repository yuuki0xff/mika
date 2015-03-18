from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse
# from shingetsu.models import *
from lib.models import *
from shingetsu.utils import *
import msgqueue
from binascii import *

__all__ = 'ping node join bye have get head update recent'.split()

class ping(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		response.write("PONG\n"+str(addr))
		s = Session()
		if not Node.getThisNode(s, addr).first():
			s.add(Node(host=addr))
			s.commit()
		s.close()
		return response

class node(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		s = Session()
		node = Node.getOtherNode(s, addr).first()
		if node is not None:
			response.write(str(node.host))
		return response

class join(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		if kwargs['node']:
			addr = kwargs['node']
		response = HttpResponse()
		s = Session()
		thisNode = Node.getThisNode(s, addr).first()
		otherNode = Node.getOtherNode(s, addr).first()
		linkedNodeCount = Node.getLinkedNode(s).count()

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
		thisNode = Node.getThisNode(s, addr).first()
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
			if Thread.get(s, title=title).value(Thread.id):
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
			s = Session()
			title = a2b_hex(basename)
			thread_id = Thread.get(s, title=title).value(Thread.id)
			allRecords = Record.gets(s, thread_id, stime, etime)
			for line in record2str(allRecords, 1):
				response.write(line)
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
			s = Session()
			title = a2b_hex(basename)
			thread_id = Thread.get(s, title=title).value(Thread.id)
			allRecords = Record.gets(s, thread_id, stime, etime)
			for line in record2str(allRecords, 0):
				response.write(line)
		return response

class update(View):
	pass

class recent(View):
	pass
