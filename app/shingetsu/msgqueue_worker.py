from app.shingetsu.utils import httpGet, str2recordInfo
from lib.models import Session, Thread, Record, Node, MessageQueue
from lib.msgqueue import multiThread, notify
from urllib.error import URLError
from binascii import a2b_hex, b2a_hex
from queue import Queue
from random import shuffle
import core.settings as settings
import logging
log = logging.getLogger(__name__)

def getRecord(msg):
	with Session() as s:
		addr, thread_id, hex_id, atime = msg.msg.split()
		thread_id = int(thread_id)
		bin_id = a2b_hex(hex_id)
		atime = int(atime)

		if Record.get(s, thread_id, bin_id, atime).value(Record.record_id):
			log.isEnabledFor(logging.INFO) and log.info('getRecord: NOP {}/{}/{} {}'.format(thread_id, atime, hex_id, addr))
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
				log.isEnabledFor(logging.INFO) and log.info('getRecord: Add {}/{}/{} {}'.format(thread_id, timestamp, b2a_hex(bin_id), addr))
			s.commit()
		except URLError as e:
			log.isEnabledFor(logging.INFO) and log.info('getRecord: Fail {}/{}/{} {} {}'.format(thread_id, atime, hex_id, addr, str(e)))
			return False
		return True

def _updateRecord_httpGetWrapper(host, fname, time, hex_id, thread_id):
	try:
		url = 'http://{}/update/{}/{}/{}/{}'.format(host, fname, time, hex_id, settings.NODE_NAME)
		httpGet(url)
		log.isEnabledFor(logging.INFO) and log.info('updateRecord: Success {}/{}/{} {}'.format(thread_id, time, hex_id, host,))
		return True
	except URLError as e:
		log.isEnabledFor(logging.INFO) and log.info('updateRecord: Error {}/{}/{} {} {}'.format(thread_id, time, hex_id, host, str(e),))
		return False

def updateRecord(msg):
	with Session() as s:
		addr, thread_id, hex_id, atime = msg.msg.split()
		thread_id = int(thread_id)
		bin_id = a2b_hex(hex_id)
		atime = int(atime)
		filename = Thread.getFileName(Thread.get(s, id=thread_id).value(Thread.title))

		if Record.get(s, thread_id, bin_id, atime).value(Record.record_id) is None:
			log.isEnabledFor(logging.INFO) and log.info('updateRecord: Skip {}/{}/{} {}'.format(thread_id, atime, hex_id, addr))
			return False

		queue = Queue()
		for host in Node.getLinkedNode(s).values(Node.host):
			queue.put((
				host.host, filename, atime, hex_id, thread_id,
				))
	log.isEnabledFor(logging.INFO) and log.info('updateRecord: Run {}/{}/{} {}'.format(thread_id, atime, hex_id, addr))
	multiThread(_updateRecord_httpGetWrapper, queue, maxWorkers=settings.MAX_CONNECTIONS)
	return True

def _getRecent_worker(host):
	urlSuffix = '/recent/0-'
	try:
		recent = httpGet('http://' + host + urlSuffix)
	except URLError:
		return
	with Session() as s:
		fileNames = []
		for line in str2recordInfo(recent):
			timestamp, recordId, fileName = line[0:3]
			if fileName.split('_')[0] not in ('thread'):
				continue
			fileNames.append(fileName)

		for fileName in sorted(fileNames):
			thread = Thread.get(s, title=a2b_hex(fileName.split('_')[1])).first()
			if thread is None:
				continue
			log.isEnabledFor(logging.INFO) and log.info('getRecent: found {} {}'.format(thread.id, host))
			MessageQueue.enqueue(s, msgtype='get_thread', msg=' '.join((host, fileName)))
		s.commit()
	notify()

def getRecent(msg):
	log.isEnabledFor(logging.INFO) and log.info('getRecent: {}'.format(msg.msg))

	with Session() as s:
		queue = Queue()
		for node in Node.getLinkedNode(s).all():
			queue.put((node.host,))
	multiThread(_getRecent_worker, queue, maxWorkers=settings.MAX_CONNECTIONS)

def getThread(msg):
	log.isEnabledFor(logging.INFO) and log.info('getThread: {}'.format(msg.msg))

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

def _doPing_worker(host):
	try:
		httpGet('http://' + host + '/ping')
	except URLError:
		pass

def doPing(msg):
	with Session() as s:
		queue = Queue()
		for node in Node.getLinkedNode(s).all():
			queue.put((node.host,))
		multiThread(_doPing_worker, queue, maxWorkers=settings.MAX_CONNECTIONS)
		MessageQueue.enqueue(s, msgtype='join', msg='init')

def _joinNetwork_findNodeWorker(host):
	try:
		newHost = httpGet('http://' + host + '/node').strip()
		with Session() as s:
			if Node.getThisNode(s, newHost).first():
				return
			Node.add(s, newHost)
			s.commit()
	except URLError:
		pass

def _joinNetwork_joinWorker(host):
	try:
		response = httpGet('http://' + host + '/join/' + settings.NODE_NAME).splitlines()
		if response[0] != 'WELCOME':
			return

		with Session() as s:
			node = Node.getThisNode(s, host).first()
			if node:
				node.linked = True
			else:
				Node.add(s, host)
			s.commit()

		if len(response) == 2:
			newHost = response[1]
			with Session() as s:
				if Node.getThisNode(s, newHost).first():
					return
				Node.add(s, newHost)
				s.commit()
	except URLError:
		pass

def _joinNetwork_doByeByeWorker(host):
	try:
		httpGet('http://' + host + '/bye/' + settings.NODE_NAME)
	except URLError:
		pass

def joinNetwork(msg):
	with Session() as s:
		queue = Queue()
		for node in Node.getInitNode(s).all():
			queue.put((node.host,))
	multiThread(_joinNetwork_findNodeWorker, queue, maxWorkers=settings.MAX_CONNECTIONS)

	with Session() as s:
		linkedNodeCount = Node.getLinkedNode(s).count()
		changeNodeCount = int(max(0, settings.MAX_NODES - linkedNodeCount) + settings.MAX_NODES/5)

		queue = Queue()
		for node in Node.getNotLinkedNode(s).limit(changeNodeCount).all():
			queue.put((node.host,))
	multiThread(_joinNetwork_joinWorker, queue, maxWorkers=settings.MAX_CONNECTIONS)

	with Session() as s:
		linkedNodes = Node.getLinkedNode(s).all()
		shuffle(linkedNodes)

		queue = Queue()
		for i in range(max(0, Node.getLinkedNode(s).count() - settings.MAX_NODES)):
			queue.put((linkedNodes[i].host,))
	multiThread(_joinNetwork_doByeByeWorker, queue, maxWorkers=settings.MAX_CONNECTIONS)


