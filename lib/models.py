from sqlalchemy import create_engine
import sqlalchemy.sql.expression as sql_func
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from datetime import datetime
from binascii import b2a_hex, a2b_hex
from base64 import b64decode
from lib.utils import timestamp2str, timestamp2datetime, datetime2timestamp, str2timestamp
import time
from core import settings

engine = create_engine(settings.DB_ADDRESS, echo=False)
Base = declarative_base()
_ScopedSession = scoped_session(sessionmaker(bind=engine))
Base.metadata.bind = engine

@contextmanager
def Session():
	s = _ScopedSession()
	try:
		yield s
	except:
		s.rollback()
		raise
	finally:
		s.close()

__all__ = "Session".split()
tableNames = [
		'Thread',
		'Record',
		'RecordRemoved',
		'RecordAttach',
		'RecordRaw',
		'Recent',
		'Tagname',
		'Tag',
		'Node',
		'MessageType',
		'MessageQueue',
		]
__all__ = __all__ + tableNames

class Thread(Base):
	__tablename__ = 'thread'
	__table_args__ = {'autoload': True}
	@classmethod
	def add(cls, session, title):
		thread = Thread()
		thread.title = title
		session.add(thread)
		return thread
	@classmethod
	def get(cls, session, **kwargs):
		query = session.query(cls)
		if 'id' in kwargs:
			query = query.filter(Thread.id == kwargs['id'])
		elif 'title' in kwargs:
			query = query.filter(Thread.title == kwargs['title'])
		else:
			assert(0)
		return query
	@classmethod
	def getFileName(cls, title):
		# 16進数表現のA-Fは大文字でなければならない
		return 'thread_' + b2a_hex(title.encode('utf-8')).decode('utf-8').upper()
	@classmethod
	def gets(cls, session, limit=None, stime=None, etime=None, title=None):
		query = session.query(cls)
		if stime is not None:
			if stime == 0:
				exp = sql_func.or_(
						cls.timestamp >= timestamp2str(1),
						cls.timestamp == timestamp2str(stime),
						)
			else:
				exp = cls.timestamp >= timestamp2str(stime)
			query = query.filter(exp)
		if etime is not None:
			if etime == 0:
				exp = cls.timestamp == timestamp2str(etime)
			else:
				exp = cls.timestamp <= timestamp2str(etime)
			query = query.filter(exp)
		if title is not None:
			query = query.filter(Thread.title == title)
		if limit is not None:
			query = query.limit(int(limit))
		return query

class Record(Base):
	__tablename__ = 'record'
	__table_args__ = {'autoload': True}

	@classmethod
	def gets(cls, session, thread_id, stime=None, etime=None, bin_id=None, limit=None, sort=True):
		allRecords = session.query(Record).filter(Record.thread_id == thread_id)
		if stime is not None:
			Record.timestamp >= timestamp2datetime(stime)
			if stime == 0:
				stime = 1
			allRecords = allRecords.filter(Record.timestamp >= timestamp2datetime(stime))
		if etime is not None:
			if etime == 0:
				etime = 1
			allRecords = allRecords.filter(Record.timestamp <= timestamp2datetime(etime))
		if bin_id is not None:
			allRecords = allRecords.filter(Record.bin_id == bin_id)
		if sort:
			allRecords = allRecords.order_by(cls.timestamp)
		if limit is not None:
			allRecords = allRecords.limit(int(limit))
		return allRecords
	@classmethod
	def get(cls, session, thread_id, bin_id, timestamp):
		return session.query(cls)\
				.filter(
					cls.thread_id == thread_id,
					cls.bin_id == bin_id,
					cls.timestamp == timestamp2datetime(timestamp)
					)
	@classmethod
	def getFirstTime(cls, session, thread_id):
		rec = session.query(Record) \
				.filter(Record.thread_id == thread_id) \
				.order_by(Record.timestamp) \
				.first()
		if rec:
			return int(datetime2timestamp(rec.timestamp))
		return 0
	@classmethod
	def getLastTime(cls, session, thread_id):
		rec = session.query(Record) \
				.filter(Record.thread_id == thread_id) \
				.order_by(Record.timestamp.desc()) \
				.first()
		if rec:
			return int(time.mktime(rec.timestamp.timetuple()))
		return 0
	@classmethod
	def add(cls, session, thread_id, timestamp, bin_id, body):
		fields = {}
		for i in body.split('<>'):
			fieldName, fieldValue = i.split(':', 1)
			fields[fieldName] = fieldValue

		rec = Record()
		rec.thread_id = thread_id
		rec.bin_id = bin_id
		rec.timestamp = datetime.fromtimestamp(timestamp)
		rec.raw_body = body
		rec.name = fields.get('name', '')
		rec.mail = fields.get('mail', '')
		rec.body = fields.get('body', '')
		if 'remove_id' in fields:
			rec.remove_id = a2b_hex(fields.get('remove_id'))
			rec.remove_stamp = str2timestamp(fields.get('remove_stamp'))
		if 'attach' in fields:
			rec.attach = b64decode(fields['attach'])
			rec.suffix = fields['suffix']
		if 'pubkey' in fields:
			rec.pubkey = fields.get('pubkey')
			rec.sign = fields.get('sign')
			rec.target = fields.get('target')

		session.add(rec)
	@classmethod
	def delete(cls, session, thread_id, timestamp, bin_id, force=False):
		rec = cls.get(session, thread_id, bin_id, timestamp).first()
		if rec:
			session.delete(rec)
		if force or rec:
			session.add(RecordRemoved(thread_id=thread_id, timestamp=timestamp, bin_id=bin_id))

class RecordRemoved(Base):
	__tablename__ = 'record_removed'
	__table_args__ = {'autoload': True}

	@classmethod
	def get(cls, session, thread_id, timestamp, bin_id):
		return session.query(cls)\
				.filter(
					cls.thread_id == thread_id,
					cls.bin_id == bin_id,
					cls.timestamp == datetime.fromtimestamp(timestamp)
					)

class RecordAttach(Base):
	__tablename__ = 'record_removed'
	__table_args__ = {'autoload': True}

class RecordRaw(Base):
	__tablename__ = 'record_removed'
	__table_args__ = {'autoload': True}

class Recent(Base):
	__tablename__ = 'recent'
	__table_args__ = {'autoload': True}

	@classmethod
	def gets(cls, session, stime=None, etime=None):
		query = session.query(cls)
		if stime:
			query = query.filter(cls.timestamp >= stime)
		if etime:
			query = query.filter(cls.timestamp <= etime)
		return query
	@classmethod
	def get(cls, session, timestamp, binId, fileName):
		return session.query(cls).filter(
				cls.timestamp == timestamp,
				cls.bin_id == binId,
				cls.file_name == fileName,
				)
	@classmethod
	def add(cls, session, timestamp, binId, fileName):
		session.add(Recent(timestamp=datetime.fromtimestamp(timestamp), bin_id=binId, file_name=fileName))

class Tagname(Base):
	__tablename__ = 'tagname'
	__table_args__ = {'autoload': True}

class Tag(Base):
	__tablename__ = 'tag'
	__table_args__ = {'autoload': True}

class Node(Base):
	__tablename__ = 'node'
	__table_args__ = {'autoload': True}

	@classmethod
	def getThisNode(cls, session, addr):
		return session.query(cls)\
				.filter(cls.host == addr)
	@classmethod
	def getOtherNode(cls, session, addr):
		return session.query(cls)\
				.filter(cls.host != addr)
	@classmethod
	def getLinkedNode(cls, session):
		return session.query(cls)\
				.filter(cls.linked == True)

	@classmethod
	def getNotLinkedNode(cls, session):
		return session.query(cls)\
				.filter(cls.linked == False)

	@classmethod
	def getInitNode(cls, session):
		return session.query(cls)\
				.filter(cls.init == True)

	@classmethod
	def add(cls, session, addr):
		node = Node()
		node.host = addr
		node.timestamp = datetime.now()
		session.add(node)

	def updateTimestamp(self):
		self.timestamp = datetime.now()

class MessageType(Base):
	__tablename__ = 'message_type'
	__table_args__ = {'autoload': True}

	@classmethod
	def get(cls, session, id):
		return session.query(cls)\
				.filter(cls.id == id)

class MessageQueue(Base):
	__tablename__ = 'message_queue'
	__table_args__ = {'autoload': True}

	@classmethod
	def enqueue(cls, session, msgtype, msg=''):
		msgtype_id = session.query(MessageType).filter(MessageType.name == msgtype).value(MessageType.id)
		session.add(cls(msgtype_id=msgtype_id, msg=msg))
	@classmethod
	def dequeue(cls, session):
		msg = session.query(cls)\
				.filter(MessageType.id == cls.msgtype_id)\
				.order_by(MessageType.priority, cls.id)\
				.first()
		if msg:
			session.delete(msg)
		return msg
	def getTypeName(self, session):
		return MessageType.get(session, self.msgtype_id).value(MessageType.name)

