from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm.session import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

engine = create_engine('mysql+mysqlconnector://root:root@localhost/mika', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
Base.metadata.bind = engine

__all__ = "Session".split()
tableNames = [
		'Thread',
		'Record',
		'RecordPost',
		'RecordAttach',
		'RecordRemoveNotify',
		'RecordSignature',
		'RecordRaw',
		'Tagname',
		'Tag',
		'Node',
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
			allRecords = allRecords.filter(Record.timestamp <= datetime.fromtimestamp(etime))
		return allRecords
	@classmethod
	def get(cls, session, thread_id, bin_id, timestamp):
		return session.query(cls)\
				.filter(
					cls.thread_id == thread_id,
					cls.bin_id == bin_id,
					cls.timestamp == datetime.fromtimestamp(atime)
					)

class RecordPost(Base):
	__tablename__ = 'record_post'
	__table_args__ = {'autoload': True}

class RecordAttach(Base):
	__tablename__ = 'record_attach'
	__table_args__ = {'autoload': True}

class RecordRemoveNotify(Base):
	__tablename__ = 'record_remove_notify'
	__table_args__ = {'autoload': True}

class RecordSignature(Base):
	__tablename__ = 'record_signature'
	__table_args__ = {'autoload': True}

class RecordRaw(Base):
	__tablename__ = 'record_raw'
	__table_args__ = {'autoload': True}

	@classmethod
	def get(cls, session, record_id):
		return session.query(cls)\
				.filter(cls.record_id == record_id)

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

