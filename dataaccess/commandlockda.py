from datetime import datetime, timedelta
from dataaccess.utility import sqliteda
from globals import DateFormat

cmdCollection: str = 'CommandLock'
eltCollection: str = 'EliteFourLock'

#region Commands

def CheckLock(serverId: int, userId: int):
	return sqliteda.KeyExists(cmdCollection, f'{serverId}{userId}')

def AddLock(serverId: int, userId: int):
	if sqliteda.KeyExists(cmdCollection, f'{serverId}{userId}'):
		date = datetime.strptime(sqliteda.Load(cmdCollection, f'{serverId}{userId}'), DateFormat)
		if date + timedelta(minutes=5) < datetime.now():
			sqliteda.Save(cmdCollection, f'{serverId}{userId}', datetime.strftime(datetime.now(), DateFormat))
			return True
		return False
	sqliteda.Save(cmdCollection, f'{serverId}{userId}', datetime.strftime(datetime.now(), DateFormat))
	return True

def DeleteLock(serverId: int, userId: int):
	if sqliteda.KeyExists(cmdCollection, f'{serverId}{userId}'):
		sqliteda.Remove(cmdCollection, f'{serverId}{userId}')

def DeleteAllLocks():
	for key in sqliteda.GetAllKeys(cmdCollection):
		sqliteda.Remove(cmdCollection, key)
	
#endregion

#region EliteFour

def CheckEliteFourLock(serverId: int, userId: int):
	return sqliteda.KeyExists(eltCollection, f'{serverId}{userId}')

def AddEliteFourLock(serverId: int, userId: int):
	if not sqliteda.KeyExists(eltCollection, f'{serverId}{userId}'):
		sqliteda.Save(eltCollection, f'{serverId}{userId}', datetime.strftime(datetime.now(), DateFormat))

def DeleteEliteFourLock(serverId: int, userId: int):
	if sqliteda.KeyExists(eltCollection, f'{serverId}{userId}'):
		sqliteda.Remove(eltCollection, f'{serverId}{userId}')
	
#endregion