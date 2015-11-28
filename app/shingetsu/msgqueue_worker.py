from shingetsu.utils import *
from lib.models import *
from lib.msgqueue import *
from urllib.error import *
from binascii import *
from queue import Queue
import logging
log = logging.getLogger(__name__)

def getRecord(msg):
	s = Session()
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
		url = 'http://{}/update/{}/{}/{}/'.format(host, fname, time, hex_id,)
		httpGet(url)
		log.info('updateRecord[Done] {}/{}/{} {} {}'.format(thread_id, time, hex_id, host, str(e),))
		return True
	except URLError as e:
		log.info('updateRecord[Fail] {}/{}/{} {} {}'.format(thread_id, time, hex_id, host, str(e),))
		return False

def updateRecord(msg):
	s = Session()
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

