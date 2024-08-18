from datetime import datetime, timedelta
from dataaccess.utility import sqliteda
from globals import DateFormat

collection: str = 'CommandLock'

def AddLock(serverId: int, userId: int):
	if sqliteda.KeyExists(collection, f'{serverId}{userId}'):
		date = datetime.strptime(sqliteda.Load(collection, f'{serverId}{userId}'), DateFormat)
		if date + timedelta(minutes=5) < datetime.now():
			sqliteda.Save(collection, f'{serverId}{userId}', datetime.strftime(datetime.now(), DateFormat))
			return True
		return False
	sqliteda.Save(collection, f'{serverId}{userId}', datetime.strftime(datetime.now(), DateFormat))
	return True


def DeleteLock(serverId: int, userId: int):
	if sqliteda.KeyExists(collection, f'{serverId}{userId}'):
		sqliteda.Remove(collection, f'{serverId}{userId}')