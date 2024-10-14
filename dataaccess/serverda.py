from dataaccess.utility import sqliteda
from models.Server import Server

collection: str = 'Server'

def CheckServer(serverId: int):
  return sqliteda.KeyExists(collection, serverId)

def GetSingleServer(serverId: int) -> Server|None:
  return sqliteda.Load(collection, serverId)

def UpsertSingleServer(server: Server):
  sqliteda.Save(collection, server.ServerId, server)

def DeleteSingleServer(server: Server):
  sqliteda.Remove(collection, server.ServerId)

def GetServers() -> list[Server]:
  return [t for t in sqliteda.LoadAll(collection)]
