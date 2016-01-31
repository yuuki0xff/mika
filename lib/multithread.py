
import core.settings as settings
import threading

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

