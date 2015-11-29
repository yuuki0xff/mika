from lib.models import *
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
		worker(*args)

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
				s = Session()
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
				worker = workerFunc.get(msg.getTypeName(s))
				try:
					worker(msg)
				except Exception as e:
					log.error(''.join([
						'Worker died.',
						traceback.format_exc(),
						]))
			except Exception as e:
				log.critical('\n'.join([
					'Error occurs in the message loop...',
					traceback.format_exc(),
					]))
				time.sleep(3)

def notify():
	with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
		try:
			s.connect(settings.MESSAGE_QUEUE_SOCK_FILE)
		except:
			pass

def getTimer(interval, func, args=[], kwargs={}):
	def timer():
		while True:
			func(*args, **kwargs)
			time.sleep(interval)
	return timer

