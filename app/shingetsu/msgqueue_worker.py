from shingetsu.utils import *
from lib.models import *
from lib.msgqueue import *
from urllib.error import *
from binascii import *
from queue import Queue
import logging
log = logging.getLogger(__name__)

# TODO: このアドレスを外部から取得するようにする
nodename = '192.168.56.1:80+server_api'

def getRecord(msg):
	with Session() as s:
		addr, thread_id, hex_id, atime = msg.msg.split()
		thread_id = int(thread_id)
		bin_id = a2b_hex(hex_id)
		atime = int(atime)

		if Record.get(s, thread_id, bin_id, atime).value(Record.record_id):
			log.info('getRecord[NOP] {}/{}/{} {}'.format(thread_id, atime, hex_id, addr))
			return True

		title = Thread.get(s, id=thread_id).value(Thread.title)
		filename = Thread.getFileName(title)
		http_addr = 'http://{}/get/{}/{}'.format(addr, filename, atime)
		try:
			for record in str2recordInfo(httpGet(http_addr)):
				timestamp, hex_id, body = record
				bin_id = a2b_hex(hex_id)
				timestamp = int(timestamp)
				if Record.get(s, thread_id, bin_id, timestamp).first():
					continue
				Record.add(s, thread_id, timestamp, bin_id, body)
				log.info('getRecord[Add] {}/{}/{} {}'.format(thread_id, timestamp, b2a_hex(bin_id), addr))
			s.commit()
		except URLError as e:
			log.info('getRecord[Fail] {}/{}/{} {} {}'.format(thread_id, atime, hex_id, addr, str(e)))
			return False
		return True

def _updateRecord_httpGetWrapper(host, fname, time, hex_id, thread_id):
	try:
		url = 'http://{}/update/{}/{}/{}/{}'.format(host, fname, time, hex_id, nodename)
		httpGet(url)
		log.info('updateRecord[Done] {}/{}/{} {}'.format(thread_id, time, hex_id, host,))
		return True
	except URLError as e:
		log.info('updateRecord[Fail] {}/{}/{} {} {}'.format(thread_id, time, hex_id, host, str(e),))
		return False

def updateRecord(msg):
	with Session() as s:
		addr, thread_id, hex_id, atime = msg.msg.split()
		thread_id = int(thread_id)
		bin_id = a2b_hex(hex_id)
		atime = int(atime)
		filename = Thread.getFileName(Thread.get(s, id=thread_id).value(Thread.title))

		if Record.get(s, thread_id, bin_id, atime).value(Record.record_id) is None:
			log.info('updateRecord[NOP] {}/{}/{} {}'.format(thread_id, atime, hex_id, addr))
			return False

		log.info('updateRecord[Run] {}/{}/{}'.format(thread_id, atime, hex_id,))
		queue = Queue()
		for host in Node.getLinkedNode(s).values(Node.host):
			queue.put((
				host.host, filename, atime, hex_id, thread_id,
				))
	multiThread(_updateRecord_httpGetWrapper, queue, maxWorkers=settings.MAX_CONNECTIONS)
	return True

def _getRecent_worker(host):
	urlSuffix = '/recent/0-'
	try:
		recent = httpGet('http://' + host + urlSuffix)
	except URLError as e:
		return
	with Session() as s:
		for line in str2recordInfo(recent):
			timestamp, recordId, fileName = line[0:3]
			if fileName.split('_')[0] not in ('thread'):
				continue

			thread = Thread.get(s, filename=fileName).first()
			if thread is None:
				continue
			MessageQueue.enqueue(s, msgtype='get_thread', msg=' '.join((host, fileName)))
		s.commit()
	notify()

def getRecent(msg):
	with Session() as s:
		queue = Queue()
		for node in Node.getLinkedNode(s).all():
			queue.put((node.host,))
	multiThread(_getRecent_worker, queue, maxWorkers=settings.MAX_CONNECTIONS)

def getThread(msg):
	with Session() as s:
		host, fileName = msg.msg.split()
		response = httpGet('http://{}/head/{}/0-'.format(host, fileName))

		threadTitle = a2b_hex(fileName.split('_')[1]).decode('utf-8')
		thread = Thread.get(s, title=threadTitle).first()
		if thread is None:
			return
		for timestamp, recordId in str2recordInfo(response):
			timestamp = int(timestamp)
			if Record.get(s, thread.id, a2b_hex(recordId), timestamp).first() is None:
				msg = ' '.join((host, str(thread.id), recordId, str(timestamp)))
				MessageQueue.enqueue(s, msgtype='get_record', msg=msg)
		s.commit()
		notify()

