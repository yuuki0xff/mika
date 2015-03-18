from shingetsu.utils import *
from lib.models import *
from lib.msgqueue import *
from urllib.error import *
from binascii import *
from queue import Queue

def getRecord(msg):
	s = Session()
	addr, thread_id, hex_id, atime = msg.msg.split()
	thread_id = int(thread_id)
	bin_id = a2b_hex(hex_id)
	atime = int(atime)

	if Record.get(s, thread_id, bin_id, atime).value(Record.record_id):
		return True

	title = Thread.get(s, id=thread_id).value(Thread.title)
	filename = Thread.getFileName(title)
	http_addr = 'http://{}/get/{}/{}'.format(addr, filename, atime)
	try:
		for record in str2recordInfo(thread_id, httpGet(http_addr)):
			timestamp, hex_id, body = record
			bin_id = a2b_hex(hex_id)
			if Record.get(s, thread_id, bin_id, record[0]).first():
				continue
			Record.add(s, thread_id, timestamp, bin_id, body)
		s.commit()
	except URLError as e:
		return False
	return True

def updateRecord(msg):
	s = Session()
	addr, thread_id, hex_id, atime = msg.msg.split()
	thread_id = int(thread_id)
	bin_id = a2b_hex(hex_id)
	atime = int(atime)
	filename = Thread.getFileName(Thread.get(s, id=thread_id).value(Thread.title))

	if Record.get(s, thread_id, bin_id, atime).value(Record.record_id) is None:
		return False

	queue = Queue()
	for host in Node.getLinkedNode(s).values(Node.host):
		http_addr = 'http://{}/update/{}/{}/{}/'.format(host.host, filename, atime, hex_id)
		queue.put((http_addr,))
	multiThread(httpGet, queue, maxWorkers=settings.MAX_CONNECTIONS)
	return True

def getAndUpdateRecord(addr, thread_id, hex_id, atime):
	s = Session()
	msg = ' '.join((addr, str(thread_id), str(hex_id), str(atime)))
	MessageQueue.enqueue(s, msgtype='get_record', msg=msg)
	MessageQueue.enqueue(s, msgtype='update_record', msg=msg)
	s.commit()
	notify()

