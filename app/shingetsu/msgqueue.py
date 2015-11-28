
from lib.models import *

def getAndUpdateRecord(addr, thread_id, hex_id, timestamp):
	s = Session()
	msg = ' '.join((addr, str(thread_id), str(hex_id), str(timestamp)))
	if addr is not None:
		MessageQueue.enqueue(s, msgtype='get_record', msg=msg)
	MessageQueue.enqueue(s, msgtype='update_record', msg=msg)
	s.commit()
	notify()

