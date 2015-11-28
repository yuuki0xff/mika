
from lib.models import *
import time
from base64 import b64encode, b64decode
from datetime import datetime
from binascii import *
from urllib.request import urlopen, Request
import io
import gzip
import hashlib
from core import settings
import logging
log = logging.getLogger(__name__)

def splitFileName(fname):
	return fname.split('_', 2)

def record2str(query, include_body=1):
	s = Session()
	if not include_body:
		query = query.with_entities(Record.bin_id, Record.timestamp, Record.raw_body)
	for r in query:
		if not include_body:
			yield '<>'.join((
					str(int(time.mktime(r.timestamp.timetuple()))),
					str(b2a_hex(r.bin_id).decode('utf-8')),
				))+'\n'
			continue
		yield '<>'.join((
				str(int(time.mktime(r.timestamp.timetuple()))),
				str(b2a_hex(r.bin_id).decode('utf-8')),
				r.raw_body,
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

def httpGet(http_addr):
	log.debug('HTTP_GET '+http_addr)
	request = urlopen(http_addr, timeout=settings.HTTP_TIMEOUT)
	with request as httpsock:
		return httpsock.read().decode('utf-8')

def str2recordInfo(string):
	for record in string.splitlines():
		# timestamp, bin_id_hex, body
		yield record.split('<>', 2)

def makeRecordStr(timestamp, name, mail, body, attach=None, suffix=None):
	dic = {
			'name': name,
			'mail': mail,
			'body': body,
			}
	if attach:
		dic['attach'] = b64encode(attach)
		dic['suffix'] = suffix

	arr = []
	for key in dic.keys():
		val = str(dic[key]).replace('<', '&lt;').replace('>', '&gt;')
		arr.append(str(key) +":"+ val)

	record_body = '<>'.join(arr)
	h = hashlib.md5()
	h.update(record_body.encode('utf-8'))
	record_id = h.hexdigest()
	record = "{}<>{}<>{}".format(
			str(int(timestamp)),
			record_id,
			record_body
			)
	return record

