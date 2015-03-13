from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.session import Session, sessionmaker

engine = create_engine('mysql+mysqlconnector://root:root@localhost/mika', echo=False)
Base = automap_base()
Base.prepare(engine, reflect=True)
Session = sessionmaker(bind=engine)

__all__ = "Session Base tableNames".split()
tableNames = []

# for table in 'thread record record_post record_attach record_remove record_signature tagname tag'.split():
for table in 'thread record tagname tag'.split():
	className = table.capitalize()
	exec('{className} = Base.classes.{tableName}'.format(
		className = className,
		tableName = table,
		))
	tableNames.append(className)
	__all__.append(className)

