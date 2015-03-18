#!/usr/bin/env python3
import settings
import msgqueue
import shingetsu.msgqueue_worker as shingetsu_worker

workerFunc = {
		'get_record': shingetsu_worker.getRecord,
		'update_record': shingetsu_worker.updateRecord,
		}
msgqueue.dispatcher(workerFunc)

