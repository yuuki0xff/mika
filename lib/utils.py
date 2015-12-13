
from datetime import datetime
import time

def timestamp2str(ts):
	if ts == 0 or ts is None:
		return '0000-00-00 00:00:00'
	else:
		return str(timestamp2datetime(ts))

def str2timestamp(s):
	if s is None:
		return 0
	return int(s)

def datetime2timestamp(dt):
	if dt is None:
		return 0
	return int(time.mktime(dt.timetuple()))

def timestamp2datetime(ts):
	return datetime.fromtimestamp(ts)

