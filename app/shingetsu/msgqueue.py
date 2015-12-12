
from lib.models import Session, MessageQueue
from lib.msgqueue import notify
import core.settings as settings
import logging
log = logging.getLogger(__name__)

def getAndUpdateRecord(addr, thread_id, hex_id, timestamp):
	log.isEnabledFor(logging.INFO) and log.info(
			'getAndUpdateRecord: threadId:{} hexId:{} timestamp:{}'.format(thread_id, hex_id, timestamp))

	with Session() as s:
		timestamp = int(float(timestamp))
		msg = ' '.join((addr, str(thread_id), str(hex_id), str(timestamp)))
		if addr is not None:
			MessageQueue.enqueue(s, msgtype='get_record', msg=msg)

		msg = ' '.join((str(thread_id), str(hex_id), str(timestamp), settings.NODE_NAME))
		MessageQueue.enqueue(s, msgtype='update_record', msg=msg)
		s.commit()

	notify()

def updateRecord(thread_id, hex_id, timestamp, nodeName=settings.NODE_NAME):
	log.isEnabledFor(logging.INFO) and log.info(
			'updateRecord: threadId:{} hexId:{} timestamp:{}'.format(thread_id, hex_id, timestamp))

	with Session() as s:
		timestamp = str(int(float(timestamp)))
		hex_id = str(hex_id)
		thread_id = str(thread_id)
		msg = ' '.join((thread_id, hex_id, timestamp, nodeName))
		MessageQueue.enqueue(s, msgtype='update_record', msg=msg)
		s.commit()

	notify()

