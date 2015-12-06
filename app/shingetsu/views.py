
from django.views.generic import View
from django.http import HttpResponse
from lib.models import Session, Node, Thread, Record, Tag, Tagname
from app.shingetsu.utils import splitFileName, record2str, getTimeRange
from app.shingetsu import msgqueue
from binascii import a2b_hex
from lib.utils import datetime2timestamp

__all__ = 'ping node join bye have get head update recent'.split()

class ping(View):
	def dispatch(self, request, *args, **kwargs):
		addr = request.META['REMOTE_ADDR']
		response = HttpResponse()
		response.write("PONG\n"+str(addr))
		return response

class node(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			addr = request.META['REMOTE_ADDR']
			response = HttpResponse()
			node = Node.getOtherNode(s, addr).first()
			if node is not None:
				response.write(str(node.host))
			return response

class join(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			addr = kwargs['node'].replace('+', '/')
			if addr.startswith(':') or addr.startswith('/'):
				addr = request.META['REMOTE_ADDR'] + addr
			response = HttpResponse()
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
		with Session() as s:
			addr = kwargs['node'].replace('+', '/')
			if addr.startswith(':') or addr.startswith('/'):
				addr = request.META['REMOTE_ADDR'] + addr
			response = HttpResponse()
			thisNode = Node.getThisNode(s, addr).first()
			if thisNode:
				thisNode.linked = False
				s.commit()
				response.write('BYEBYE')
			return response

class have(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			prefix, basename = kwargs['file'].split('_')
			response = HttpResponse()
			if prefix=='thread':
				title = a2b_hex(basename)
				if Thread.get(s, title=title).value(Thread.id):
					response.write('YES')
					return response
			response.write('NO')
			return response

class get(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			prefix, basename = splitFileName(kwargs['file'])
			stime, etime = getTimeRange(
					kwargs.get('time'),
					kwargs.get('stime'),
					kwargs.get('etime'),
					)
			response = HttpResponse()
			if prefix=='thread':
				title = a2b_hex(basename)
				thread_id = Thread.get(s, title=title).value(Thread.id)
				allRecords = Record.gets(s, thread_id, stime, etime)
				for line in record2str(allRecords, 1):
					response.write(line)
			return response

class head(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			prefix, basename = splitFileName(kwargs['file'])
			stime, etime = getTimeRange(
					kwargs.get('time'),
					kwargs.get('stime'),
					kwargs.get('etime'),
					)
			response = HttpResponse()
			if prefix=='thread':
				title = a2b_hex(basename)
				thread_id = Thread.get(s, title=title).value(Thread.id)
				allRecords = Record.gets(s, thread_id, stime, etime)
				for line in record2str(allRecords, 0):
					response.write(line)
			return response

class update(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			prefix, basename = splitFileName(kwargs['file'])
			title = a2b_hex(basename)
			atime = int(kwargs['time'])
			id_hex = kwargs['id']
			addr = kwargs['node'].replace('+', '/')
			if addr.startswith(':') or addr.startswith('/'):
				addr = request.META['REMOTE_ADDR'] + addr
			response = HttpResponse()
			if prefix=='thread':
				thread_id = Thread.get(s, title=title).value(Thread.id)
				if not thread_id:
					return response
				msgqueue.getAndUpdateRecord(addr, thread_id, id_hex, atime)
			return response

class recent(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			response = HttpResponse()
			if kwargs.get('time') is not None:
				query = Thread.gets(s, time=int(kwargs['time']))
			else:
				args = {}
				args['stime'] = 0
				if kwargs.get('stime') is not None:
					args['stime'] = int(kwargs['stime'])
				if kwargs.get('etime') is not None:
					args['etime'] = int(kwargs['etime'])
				query = Thread.gets(s, **args)
			for thread_id, stamp, title in query.values(Thread.id, Thread.timestamp, Thread.title):
				id = 'thread'
				fname = Thread.getFileName(title)
				tags = []
				for tag in s.query(Tagname.name).filter(
						Tag.thread_id==thread_id,
						Tag.tag_id==Tagname.id
						):
					tags.append(tag)
				line = '<>'.join([
					str(datetime2timestamp(stamp)), id, fname,
					] + tags)+'\n'
				response.write(line)
			return response

