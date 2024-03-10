import logging
from sqlitedict import SqliteDict

errorLog = logging.getLogger('error')
cacheFile = "dataaccess/utility/cache.sqlite3"

def Save(key: str, value):
	try:
		with SqliteDict(cacheFile) as mydict:
			mydict[str(key)] = value
			mydict.commit()
	except Exception as ex:
		errorLog.error(f'Sqlite Save Error: {ex}')

def Load(key: str):
	try:
		with SqliteDict(cacheFile) as mydict:
			value = mydict[key] if str(key) in [k for k in mydict.keys()] else None
		return value
	except Exception as ex:
		errorLog.error(f'Sqlite Load Error: {ex}')

def Remove(key: str):
	try:
		with SqliteDict(cacheFile) as mydict:
			mydict.__delitem__(key)
			mydict.commit()
	except Exception as ex:
		errorLog.error(f'Sqlite Remove Error: {ex}')
