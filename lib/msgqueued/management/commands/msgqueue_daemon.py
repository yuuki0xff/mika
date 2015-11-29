from django.core.management.base import BaseCommand, CommandError
import core.settings
import msgqueue
import shingetsu.msgqueue_worker as shingetsu_worker
from lib.models import *
from lib.msgqueue import *
import threading
import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
	args = 'start'
	def handle(self, *args, **options):
		log.info('start Message Queeue Daemon.')
		workerFunc = {
				'get_record': shingetsu_worker.getRecord,
				'update_record': shingetsu_worker.updateRecord,
				'get_thread': shingetsu_worker.getThread,
				'get_recent': shingetsu_worker.getRecent,
				}
		def recentTimer(**kwargs):
			with Session() as s:
				MessageQueue.enqueue(s, msgtype='get_recent', msg='')
				s.commit()
				notify()
		threading.Thread(target=getTimer(1, recentTimer)).start()
		msgqueue.dispatcher(workerFunc)
		log.info('stop Message Queue Daemoon.')

