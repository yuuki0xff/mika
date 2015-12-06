from django.core.management.base import BaseCommand
from core import settings
from lib import msgqueue
import app.shingetsu.msgqueue_worker as shingetsu_worker
import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
	args = 'start'
	def handle(self, *args, **options):
		log.info('start Message Queeue Daemon.')
		workerFunc = {
				'join': shingetsu_worker.joinNetwork,
				'ping': shingetsu_worker.doPing,
				'get_record': shingetsu_worker.getRecord,
				'update_record': shingetsu_worker.updateRecord,
				'get_thread': shingetsu_worker.getThread,
				'get_recent': shingetsu_worker.getRecent,
				}

		# メッセージスケジューラを呼び出す
		msgqueue.messageScheduler(msgtype='get_recent', msg='', interval=settings.RECENT_INTERVAL).start()
		msgqueue.messageScheduler(msgtype='ping', msg='', interval=settings.PING_INTERVAL).start()
		msgqueue.messageScheduler(msgtype='join', msg='', interval=settings.JOIN_INTERVAL).start()

		msgqueue.dispatcher(workerFunc)
		log.info('stop Message Queue Daemoon.')

