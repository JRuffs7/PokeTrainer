import logging
from sqlitedict import SqliteDict

errorLog = logging.getLogger('error')
cacheFile = "dataaccess/utility/cache.sqlite3"

def Save(table: str, key: str, value):
	try:
		with SqliteDict(cacheFile, tablename=table) as mydict:
			mydict[str(key)] = value
			mydict.commit()
	except Exception as ex:
		errorLog.error(f'Sqlite Save Error: {ex}')

def Load(table: str, key: str):
	try:
		with SqliteDict(cacheFile, tablename=table) as mydict:
			value = mydict[key] if str(key) in [k for k in mydict.keys()] else None
		return value
	except Exception as ex:
		errorLog.error(f'Sqlite Load Error: {ex}')

def Remove(table: str, key: str):
	try:
		with SqliteDict(cacheFile, tablename=table) as mydict:
			mydict.__delitem__(key)
			mydict.commit()
	except Exception as ex:
		errorLog.error(f'Sqlite Remove Error: {ex}')
