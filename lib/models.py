from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.session import Session, sessionmaker

engine = create_engine('mysql+mysqlconnector://root:root@localhost/mika', echo=False)
Base = automap_base()
Base.prepare(engine, reflect=True)
Session = sessionmaker(bind=engine)

__all__ = "Session Base tableNames".split()
tableNames = []

for table in 'thread record record_post record_attach record_remove_notify record_signature tagname tag node'.split():
	className = ''.join([s.capitalize() for s in table.split('_')])
	exec('{className} = Base.classes.{tableName}'.format(
		className = className,
		tableName = table,
		))
	tableNames.append(className)
	__all__.append(className)

