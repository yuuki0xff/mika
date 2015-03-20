from lib.models import *
import core.settings as settings
import threading
import socket
import time
import os
import traceback

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
		os.remove(settings.MESSAGE_QUEUE_SOCK_FILE)
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
					print('Worker died.')
					print('='*40)
					traceback.print_exc()
					print('='*40)
			except Exception as e:
				print('Error occurs in the message loop...')
				print('='*40)
				traceback.print_exc()
				print('='*40)
				time.sleep(3)

def notify():
	with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
		try:
			s.connect(settings.MESSAGE_QUEUE_SOCK_FILE)
		except:
			pass

