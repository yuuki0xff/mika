
from django.views.generic import View
from django.http import HttpResponse, HttpResponseBadRequest
from lib.models import Session, Node, Thread, Record, RecordRaw, Recent
from app.shingetsu.utils import splitFileName, getTimeRange
from app.shingetsu.error import BadFileNameException, BadTimeRange
from app.shingetsu import msgqueue
from sqlalchemy.exc import IntegrityError
import sqlalchemy.sql as sql
from binascii import a2b_hex, b2a_hex
import binascii
from lib.utils import datetime2timestamp
from core import settings
import logging
log = logging.getLogger(__name__)

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

			# node: エラーの少ないノードを優先
			node = Node.getOtherNode(s, addr).order_by(Node.error_count).first()
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
			# otherNode: エラーの少ないノードを優先
			otherNode = Node.getOtherNode(s, addr).order_by(Node.error_count).first()
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
				query = sql.select([
						Record.timestamp,
						Record.bin_id,
						RecordRaw.raw_body,
					]).where(sql.and_(*(
						[
							Thread.id == Record.thread_id,
							Thread.id == RecordRaw.thread_id,
							Record.timestamp == RecordRaw.timestamp,
							Record.bin_id == RecordRaw.bin_id,
						] +
						Thread.getFilter(title=title) +
						Record.getFilter(stime=stime, etime=etime)
					))).order_by(Record.timestamp)

				for row in s.execute(query):
					response.write(
							str(datetime2timestamp(row[0])) + '<>' +
							b2a_hex(row[1]).decode('ascii') + '<>' +
							row[2] + '\n')
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
				query = sql.select([
						Record.timestamp,
						Record.bin_id,
					]).where(sql.and_(*(
						[Thread.id == Record.thread_id] +
						Thread.getFilter(title=title) +
						Record.getFilter(stime=stime, etime=etime)
					))).order_by(Record.timestamp)

				for row in s.execute(query):
					response.write(
							str(datetime2timestamp(row[0])) + '<>' +
							b2a_hex(row[1]).decode('ascii') + '\n')
			return response

class update(View):
	def dispatch(self, request, *args, **kwargs):
		with Session() as s:
			try:
				fileName = kwargs['file'].upper()
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
				try:
					Recent.add(s, timestamp=atime, binId=id_bin, fileName=fileName)
					s.commit()
				except IntegrityError as e:
					s.rollback()
					log.isEnabledFor(logging.INFO) and log.info(str(e))
					return response
				thread_id = Thread.get(s, title=title).value(Thread.id)
				if thread_id:
					msgqueue.getAndUpdateRecord(addr, thread_id, id_hex, atime)
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

