
from lib.models import *
import time
# from base64 import b64encode, b64decode
from datetime import datetime
from binascii import *

def splitFileName(fname):
	return fname.split('_', 2)

def record2str(query, include_body=1):
	s = Session()
	if not include_body:
		query = query.with_entities(Record.bin_id, Record.timestamp)
	for r in query:
		rr = RecordRaw.get(s, r.id).one()
		yield '<>'.join((
				str(int(time.mktime(r.timestamp.timetuple()))),
				str(b2a_hex(rr.md5).decode('utf-8')),
				rr.body,
			))+'\n'

def getTimeRange(atime, starttime, endtime):
	if atime:
		return (int(atime), int(atime))
	if starttime:
		if endtime:
			return (int(starttime), int(endtime))
		now = time.mktime(datetime.now().timetuple())
		return (int(starttime), now)
	else:
		if endtime:
			return (0, int(endtime))
		raise 'ERROR'

