from app.shingetsu.utils import httpGet, str2recordInfo
from lib.models import Session, Thread, Record, Node, MessageQueue
from lib.msgqueue import multiThread, notify
from urllib.error import URLError
from binascii import a2b_hex, b2a_hex
import binascii
from queue import Queue
from random import shuffle
import core.settings as settings
import logging
import time
import sqlalchemy.exc
log = logging.getLogger(__name__)

def getRecord(msg):
	with Session() as s:
		if len(msg.msg.split()) == 4:
			mode = 'single'
			addr, thread_id, hex_id, atime = msg.msg.split()
			thread_id = int(thread_id)
			bin_id = a2b_hex(hex_id)
			atime = int(atime)
		else:
			mode = 'multi'
			addr, thread_id, timeRange = msg.msg.split()

		if mode == 'single' and Record.get(s, thread_id, bin_id, atime).value(Record.record_id):
			log.isEnabledFor(logging.INFO) and log.info('getRecord: NOP {}/{}/{} {}'.format(thread_id, atime, hex_id, addr))
			return True

		title = Thread.get(s, id=thread_id).value(Thread.title)
		filename = Thread.getFileName(title)
		if mode == 'single':
			http_addr = 'http://{}/get/{}/{}'.format(addr, filename, atime)
		else:
			http_addr = 'http://{}/get/{}/{}'.format(addr, filename, timeRange)
		try:
			for record in str2recordInfo(httpGet(http_addr)):
				try:
					timestamp, hex_id, body = record
					bin_id = a2b_hex(hex_id)
				except binascii.Error as e:
					log.isEnabledFor(logging.INFO) and log.info('getRecord: Fail {} {} {}'.format(thread_id, http_addr, str(e)))
					continue
				try:
					timestamp = int(timestamp)
					if Record.get(s, thread_id, bin_id, timestamp).first():
						continue
					Record.add(s, thread_id, timestamp, bin_id, body)
					log.isEnabledFor(logging.INFO) and log.info('getRecord: Add {}/{}/{} {}'.format(thread_id, timestamp, b2a_hex(bin_id), addr))
					s.commit()
				except (binascii.Error, sqlalchemy.exc.StatementError) as e:
					log.isEnabledFor(logging.INFO) and log.info('getRecord: Fail {} {} {}'.format(thread_id, http_addr, str(e)))
					s.rollback()
					Record.delete(s, thread_id, timestamp, bin_id)
					s.commit()
		except URLError as e:
			log.isEnabledFor(logging.INFO) and log.info('getRecord: Fail {} {} {}'.format(thread_id, http_addr, str(e)))
			return False
		return True

def _updateRecord_httpGetWrapper(host, fname, time, hex_id, thread_id, nodeName):
	try:
		url = 'http://{}/update/{}/{}/{}/{}'.format(host, fname, time, hex_id, nodeName)
		httpGet(url)
		log.isEnabledFor(logging.INFO) and log.info('updateRecord: Success {}/{}/{} {}'.format(thread_id, time, hex_id, host,))
		return True
	except URLError as e:
		log.isEnabledFor(logging.INFO) and log.info('updateRecord: Error {}/{}/{} {} {}'.format(thread_id, time, hex_id, host, str(e),))
		return False

def updateRecord(msg):
	with Session() as s:
		thread_id, hex_id, atime, nodeName = msg.msg.split()
		thread_id = int(thread_id)
		atime = int(atime)
		filename = Thread.getFileName(Thread.get(s, id=thread_id).value(Thread.title))

		queue = Queue()
		for host in Node.getLinkedNode(s).values(Node.host):
			queue.put((
				host.host, filename, atime, hex_id, thread_id, nodeName
				))
	log.isEnabledFor(logging.INFO) and log.info('updateRecord: Run {}/{}/{} {}'.format(thread_id, atime, hex_id, nodeName))
	multiThread(_updateRecord_httpGetWrapper, queue, maxWorkers=settings.MAX_CONNECTIONS)
	return True

def _getRecent_worker(host):
	urlSuffix = '/recent/0-'
	try:
		recent = httpGet('http://' + host + urlSuffix)
	except URLError:
		return
	with Session() as s:
		fileNames = set()
		for line in str2recordInfo(recent):
			timestamp, recordId, fileName = line[0:3]
			if fileName.split('_')[0] not in ('thread'):
				continue
			fileNames.add(fileName)

		for fileName in sorted(fileNames):
			try:
				threadTitle = a2b_hex(fileName.split('_')[1])
			except (ValueError, binascii.Error):
				continue
			thread = Thread.get(s, title=threadTitle).first()
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

	# ファイル名だけなら、全てのノードから順にスレッドを取得する
	if len(msg.msg.split()) == 1:
		fileName = msg.msg
		with Session() as s:
			for node in Node.getLinkedNode(s):
				MessageQueue.enqueue(s, msgtype='get_thread', msg=' '.join([
					node.host,
					fileName,
					]))
			s.commit()
		notify()
		return True

	with Session() as s:
		host, fileName = msg.msg.split()

		threadTitle = a2b_hex(fileName.split('_')[1]).decode('utf-8')
		thread = Thread.get(s, title=threadTitle).first()
		if thread is None:
			return

		lastTime = Record.getLastTime(s, thread.id)
		firstTime = Record.getFirstTime(s, thread.id)

		# 最新のレコードと、より古いレコードを取得する
		MessageQueue.enqueue(s, msgtype='get_record', msg=' '.join([
			host, str(thread.id),
			str(lastTime)+'-',
			]))
		if firstTime:
			MessageQueue.enqueue(s, msgtype='get_record', msg=' '.join([
				host, str(thread.id),
				'-'+str(firstTime),
				]))

		if firstTime and lastTime:
			# 未取得レコードが30%以上なら、その範囲をまとめて取得
			# 30%未満なら、一つずつ取得
			url = 'http://{}/head/{}/{}-{}'.format(
					host, fileName,
					str(firstTime),
					str(lastTime),
					)
			records = []
			notExistsRecordCount = 0
			existsRecordCount = 0
			_existsRecordCount = 0
			rate = None
			try:
				for timestamp, recordId in str2recordInfo(httpGet(url)):
					timestamp = int(timestamp)
					if Record.get(s, thread.id, a2b_hex(recordId), timestamp).first():
						if notExistsRecordCount:
							_existsRecordCount += 1
					else:
						records.append((timestamp, recordId,))
						notExistsRecordCount += 1
						existsRecordCount += _existsRecordCount
						_existsRecordCount = 0
						oldRate = rate
						rate = notExistsRecordCount / (notExistsRecordCount + existsRecordCount)

						if rate < 0.3 and oldRate >= 0.3:
							# records[0:-1]の範囲のレコードをまとめて取得
							newRecords = records.pop()
							MessageQueue.enqueue(s, msgtype='get_record', msg=' '.join([
								host, str(thread.id),
								str(records[0][0]) + '-' + str(records[-1][0]),
								]))
							records = [newRecords]
							notExistsRecordCount = 1
							existsRecordCount = 0

				if rate is None:
					pass
				elif rate >= 0.3:
					# まとめて取得
					MessageQueue.enqueue(s, msgtype='get_record', msg=' '.join([
						host, str(thread.id),
						str(records[0][0]) + '-' + str(records[-1][0]),
						]))
				else:
					# 一つずつ取得
					for timestamp, recordId in records:
						MessageQueue.enqueue(s, msgtype='get_record', msg=' '.join([
							host, str(thread.id), recordId, str(timestamp),
							]))
			except URLError as e:
					log.isEnabledFor(logging.INFO) and log.info('getThread: Fail {} {} {}'.format(thread.id, url, str(e)))

		s.commit()
		notify()

def _doPing_worker(host):
	try:
		response = httpGet('http://' + host + '/ping').splitlines()
		with Session() as s:
			node = Node.getThisNode(s, host).first()

			if response[0].strip() != 'PONG':
				node.linked = False
			else:
				node.updateTimestamp()

			if len(response) > 1:
				newNodeHost = response[1].strip()
				newNode = Node.getThisNode(s, newNodeHost).first()
				if not newNode:
					Node.add(s, newNodeHost)
			s.commit()
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
		with Session() as s:
			node = Node.getThisNode(s, host).first()
			if node:
				node.linked = False
			s.commit()
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


