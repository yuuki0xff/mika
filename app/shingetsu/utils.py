
from app.shingetsu.error import BadFileNameException, BadRecordException, BadTimeRange
from lib.utils import datetime2timestamp
from base64 import b64encode
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
import gzip
import zlib
import hashlib
from core import settings
import logging
log = logging.getLogger(__name__)

def splitFileName(fname):
	result = fname.split('_', 2)
	if len(result) != 2:
		raise BadFileNameException()
	return result

def getTimeRange(atime, starttime, endtime):
	if atime:
		return (int(atime), int(atime))
	if starttime:
		if endtime:
			return (int(starttime), int(endtime))
		now = datetime2timestamp(datetime.now())
		return (int(starttime), now)
	if endtime:
		return (0, int(endtime))
	# All variable is None.
	raise BadTimeRange()

def httpGet(http_addr):
	log.isEnabledFor(logging.DEBUG) and log.debug('HTTP_GET '+http_addr)
	headers = {
			'User-Agent': '{protocol} ({name} {version})'.format(protocol=' '.join(settings.PROTOCOLS), name=settings.APPLICATION_NAME, version=settings.VERSION),
			'Accept-Encoding': 'gzip',
			}
	request = Request(http_addr, headers=headers)
	with urlopen(request, timeout=settings.HTTP_TIMEOUT) as httpsock:
		if httpsock.info().get('Content-Encoding') == 'gzip':
			try:
				return gzip.GzipFile(fileobj=httpsock, mode='rb').read().decode('utf-8')
			except (zlib.error, OSError) as e: # OSError: CRC error
				raise URLError(e)
		else:
			return httpsock.read().decode('utf-8')

def str2recordInfo(string):
	for record in string.splitlines():
		# timestamp, bin_id_hex, body
		yield record.split('<>', 2)

def makeRecordStr(timestamp, name, mail, body, attach=None, suffix=None):
	def htmlEscape(s):
		return s.replace('&', '&amp;')\
				.replace('<', '&lt;')\
				.replace('>', '&gt;')

	dic = {}
	if name:
		dic['name'] = htmlEscape(name.strip())
	if mail:
		dic['mail'] = htmlEscape(mail.strip())
	if not body:
		raise BadRecordException()
	dic['body'] = htmlEscape(body.strip()).replace('\n', '<br>')

	if attach:
		dic['attach'] = b64encode(attach)
		dic['suffix'] = htmlEscape(suffix.strip())

	arr = []
	for key in dic.keys():
		val = str(dic[key])
		if '\n' in key or '\n' in val or '<>' in key:
			raise BadRecordException()
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

