
from django.views.generic import View
from django.http import HttpResponse, HttpResponseBadRequest
from lib.models import Session, Node, Thread, Record, Recent
from app.shingetsu.utils import splitFileName, record2str, getTimeRange
from app.shingetsu.error import BadFileNameException, BadTimeRange
from app.shingetsu import msgqueue
from sqlalchemy.exc import IntegrityError
from binascii import a2b_hex, b2a_hex
import binascii
from lib.utils import datetime2timestamp
from core import settings

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
				thisNode.updateTimestamp()
				s.commit()
			elif linkedNodeCount < settings.MAX_NODES:
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
			try:
				prefix, basename = splitFileName(kwargs['file'])
			except BadFileNameException:
				return HttpResponseBadRequest()

			response = HttpResponse()
			if prefix=='thread':
				try:
					title = a2b_hex(basename)
				except (TypeError, binascii.Error):
					return HttpResponseBadRequest()
				if Thread.get(s, title=title).value(Thread.id):
					response.write('YES')
					return response
			response.write('NO')
			return response

class get(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			try:
				prefix, basename = splitFileName(kwargs['file'])
				stime, etime = getTimeRange(
						kwargs.get('time'),
						kwargs.get('stime'),
						kwargs.get('etime'),
						)
			except (BadFileNameException, BadTimeRange):
				return HttpResponseBadRequest()

			response = HttpResponse()
			if prefix=='thread':
				try:
					title = a2b_hex(basename)
				except binascii.Error:
					return HttpResponseBadRequest()
				thread_id = Thread.get(s, title=title).value(Thread.id)
				allRecords = Record.gets(s, thread_id, stime, etime)
				for line in record2str(allRecords, 1):
					response.write(line)
			return response

class head(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			try:
				prefix, basename = splitFileName(kwargs['file'])
				stime, etime = getTimeRange(
						kwargs.get('time'),
						kwargs.get('stime'),
						kwargs.get('etime'),
						)
			except (BadFileNameException, BadTimeRange):
				return HttpResponseBadRequest()

			response = HttpResponse()
			if prefix=='thread':
				try:
					title = a2b_hex(basename)
				except binascii.Error:
					return HttpResponseBadRequest()
				thread_id = Thread.get(s, title=title).value(Thread.id)
				allRecords = Record.gets(s, thread_id, stime, etime)
				for line in record2str(allRecords, 0):
					response.write(line)
			return response

class update(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			try:
				fileName = kwargs['file']
				prefix, basename = splitFileName(kwargs['file'])
				title = a2b_hex(basename)
				atime = int(kwargs['time'])
				id_hex = kwargs['id']
				id_bin = a2b_hex(id_hex)
				addr = kwargs['node'].replace('+', '/')
			except (BadFileNameException, binascii.Error, ValueError):
				return HttpResponseBadRequest()

			if addr.startswith(':') or addr.startswith('/'):
				addr = request.META['REMOTE_ADDR'] + addr
			response = HttpResponse()
			if prefix=='thread':
				if Recent.get(s, atime, id_bin, fileName).first():
					return response
				thread_id = Thread.get(s, title=title).value(Thread.id)
				if thread_id:
					msgqueue.getAndUpdateRecord(addr, thread_id, id_hex, atime)
				try:
					Recent.add(s, timestamp=atime, binId=id_bin, fileName=fileName)
					s.commit()
				except IntegrityError:
					s.rollback()
			return response

class recent(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			response = HttpResponse()
			queryArgs = {}

			if kwargs.get('time') is not None:
				queryArgs['stime'] = int(kwargs['time'])
				queryArgs['etime'] = queryArgs['stime']
			else:
				if kwargs.get('stime') is not None:
					queryArgs['stime'] = int(kwargs['stime'])
				if kwargs.get('etime') is not None:
					queryArgs['etime'] = int(kwargs['etime'])

			result = Recent.gets(s, **queryArgs).values(Recent.timestamp, Recent.bin_id, Recent.file_name)
			for timestamp, binId, fileName in result:
				timestamp = datetime2timestamp(timestamp)
				hexId = b2a_hex(binId).decode('ascii')

				line = '<>'.join([
					str(timestamp), hexId, fileName,
					])+'\n'
				response.write(line)
			return response

