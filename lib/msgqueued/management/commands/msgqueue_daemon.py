from django.core.management.base import BaseCommand, CommandError
import core.settings
import msgqueue
import shingetsu.msgqueue_worker as shingetsu_worker
import logging
log = logging.getLogger(__name__)

class Command(BaseCommand):
	args = 'start'
	def handle(self, *args, **options):
		log.info('start Message Queeue Daemon.')
		workerFunc = {
				'get_record': shingetsu_worker.getRecord,
				'update_record': shingetsu_worker.updateRecord,
				}
		msgqueue.dispatcher(workerFunc)
		log.info('stop Message Queue Daemoon.')

