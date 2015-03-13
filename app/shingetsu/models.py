from lib.models import *

__all__ = 'Session'.split()
__all__.extend(tableNames)

for table in 'node'.split():
	className = table.capitalize()
	exec('{className} = Base.classes.{tableName}'.format(
		className = className,
		tableName = table,
		))
	tableNames.append(className)
	__all__.append(className)

