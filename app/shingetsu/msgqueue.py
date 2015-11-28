
from lib.models import *
from lib.msgqueue import *

def getAndUpdateRecord(addr, thread_id, hex_id, timestamp):
	s = Session()

	timestamp = int(float(timestamp))
	msg = ' '.join((addr, str(thread_id), str(hex_id), str(timestamp)))
	if addr is not None:
		MessageQueue.enqueue(s, msgtype='get_record', msg=msg)
	MessageQueue.enqueue(s, msgtype='update_record', msg=msg)
	s.commit()

	notify()

def updateRecord(thread_id, hex_id, timestamp):
	s = Session()

	timestamp = str(int(float(timestamp)))
	hex_id = str(hex_id)
	thread_id = str(thread_id)
	for node in Node.getLinkedNode(s).all():
		msg = ' '.join((node.host, thread_id, hex_id, timestamp))
		MessageQueue.enqueue(s, msgtype='update_record', msg=msg)
	s.commit()

	notify()

