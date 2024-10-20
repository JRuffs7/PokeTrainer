import logging
from sqlitedict import SqliteDict

errorLog = logging.getLogger('error')
cacheFile = "dataaccess/utility/locks.sqlite3"

def KeyExists(table: str, key: str):
	try:
		with SqliteDict(cacheFile, tablename=table) as mydict:
			exists = str(key) in [k for k in mydict.keys()]
		return exists
	except Exception as ex:
		errorLog.error(f'Sqlite Key Error: {ex}')
		return False

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
		return None

def LoadAll(table: str):
	try:
		with SqliteDict(cacheFile, tablename=table) as mydict:
			return [v for v in mydict.values()] or []
	except Exception as ex:
		errorLog.error(f'Sqlite LoadAll Error: {ex}')
		return []

def Remove(table: str, key: str):
	try:
		with SqliteDict(cacheFile, tablename=table) as mydict:
			mydict.__delitem__(key)
			mydict.commit()
	except Exception as ex:
		errorLog.error(f'Sqlite Remove Error: {ex}')
