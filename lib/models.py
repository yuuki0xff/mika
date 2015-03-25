from sqlalchemy import create_engine
from sqlalchemy import select
import sqlalchemy.sql.expression as sql_func
from sqlalchemy.orm.session import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from binascii import *
from utils import *

engine = create_engine('mysql+mysqlconnector://root:root@localhost/mika', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
Base.metadata.bind = engine

__all__ = "Session".split()
tableNames = [
		'Thread',
		'Record',
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
	def get(cls, session, **kwargs):
		query = session.query(cls)
		if 'id' in kwargs:
			query = query.filter(Thread.id == kwargs['id'])
		if 'title' in kwargs:
			query = query.filter(Thread.title == kwargs['title'])
		return query
	@classmethod
	def getFileName(cls, title):
		return 'thread_' + b2a_hex(title.encode('utf-8')).decode('utf-8')
	@classmethod
	def gets(cls, session, **kwargs):
		query = session.query(cls)
		if 'time' in kwargs:
			atime = kwargs['time']
			query = query.filter(cls.timestamp == timestamp2str(atime))
		if 'stime' in kwargs:
			stime = kwargs['stime']
			if stime == 0:
				exp = sql_func.or_(
						cls.timestamp >= timestamp2str(1),
						cls.timestamp == timestamp2str(stime),
						)
			else:
				exp = cls.timestamp >= timestamp2str(stime)
			query = query.filter(exp)
		if 'etime' in kwargs:
			etime = kwargs['etime']
			if etime == 0:
				exp = cls.timestamp == timestamp2str(etime)
			else:
				exp = cls.timestamp <= timestamp2str(etime)
			query = query.filter(exp)
		if 'title' in kwargs:
			query = query.filter(Thread.title == kwargs['title'])
		return query

class Record(Base):
	__tablename__ = 'record'
	__table_args__ = {'autoload': True}

	@classmethod
	def gets(cls, session, thread_id, stime, etime):
		allRecords = session.query(Record).filter(Record.thread_id == thread_id)
		if stime is not None:
			Record.timestamp >= datetime.fromtimestamp(stime)
			if stime == 0:
				stime = 1
			allRecords = allRecords.filter(Record.timestamp >= datetime.fromtimestamp(stime))
		if etime is not None:
			if etime == 0:
				etime = 1
			allRecords = allRecords.filter(Record.timestamp <= datetime.fromtimestamp(etime))
		return allRecords
	@classmethod
	def get(cls, session, thread_id, bin_id, timestamp):
		return session.query(cls)\
				.filter(
					cls.thread_id == thread_id,
					cls.bin_id == bin_id,
					cls.timestamp == datetime.fromtimestamp(timestamp)
					)
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
			rec.remove_id = fields.get('remove_id')
			rec.remove_stamp = fields.get('remove_stamp')
		if 'attach' in fields:
			rec.attach = a2b_hex(fields['attach'])
			rec.suffix = fields['suffix']
		if 'pubkey' in fields:
			rec.pubkey = fields.get('pubkey')
			rec.sign = fields.get('sign')
			rec.target = fields.get('target')

		session.add(rec)

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

