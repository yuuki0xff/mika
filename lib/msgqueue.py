from lib.models import Session, MessageQueue
import core.settings as settings
import threading
import socket
import time
import os
import traceback
import logging
log = logging.getLogger(__name__)

def _multiThreadWorker(worker, queue):
	while not queue.empty():
		args = queue.get()
		try:
			worker(*args)
		except Exception:
			log.isEnabledFor(logging.ERROR) and log.error(
					'_multiThreadWorker: worker died.\n' +
					traceback.format_exc()
					)

def multiThread(worker, queue, maxWorkers=settings.MAX_THREADS, daemon=True, join=True):
	threads = []
	for i in range(maxWorkers):
		threads.append(threading.Thread(target=_multiThreadWorker, args=(worker, queue,)))
	for t in threads:
		t.daemon = daemon
		t.start()
	if join:
		for t in threads:
			t.join()
	return threads

def dispatcher(workerFunc):
	with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
		try:
			os.remove(settings.MESSAGE_QUEUE_SOCK_FILE)
		except FileNotFoundError:
			pass
		sock.bind(settings.MESSAGE_QUEUE_SOCK_FILE)
		sock.listen(1)
		while True:
			try:
				with Session() as s:
					msg = MessageQueue.dequeue(s)
					s.commit()
				if msg is None:
					s.close()
					try:
						conn, addr = sock.accept()
						conn.close()
					except KeyboardInterrupt:
						return
					continue
				log.isEnabledFor(logging.DEBUG) and log.debug(' '.join([msg.getTypeName(s), msg.msg]))
				worker = workerFunc.get(msg.getTypeName(s))
				try:
					worker(msg)
				except Exception:
					log.error(''.join([
						'Worker died.',
						traceback.format_exc(),
						]))
			except Exception:
				log.critical('\n'.join([
					'Error occurs in the message loop...',
					traceback.format_exc(),
					]))
				time.sleep(3)

def notify():
	with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
		s.settimeout(0)
		try:
			s.connect(settings.MESSAGE_QUEUE_SOCK_FILE)
		except ConnectionError:
			pass

def messageScheduler(msgtype, msg='', interval=0, wait=0):
	assert(interval > 0 or wait > 0)

	def timer():
		if wait:
			time.sleep(wait)
		while True:
			with Session() as s:
				log.isEnabledFor(logging.DEBUG) and log.debug(
						'timer[{}] {}'.format(msgtype, msg))
				MessageQueue.enqueue(s, msgtype=msgtype, msg=msg)
				s.commit()
			notify()
			if not interval:
				break
			time.sleep(interval)
	return threading.Thread(target=timer)

