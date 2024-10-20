from dataaccess.utility import mongodb, sqliteda
from globals import to_dict
from models.Server import Server

collection: str = 'Server'

def CheckServer(serverId: int):
  return mongodb.NumberOfDocs(collection, {
    'ServerId': serverId
  }) == 1

def GetSingleServer(serverId: int) -> Server|None:
  server = mongodb.GetSingleDoc(collection, {'ServerId': serverId})
  return Server.from_dict(server) if server else None

def UpsertSingleServer(server: Server):
  mongodb.UpsertSingleDoc(collection, 
    {'ServerId': server.ServerId},
    to_dict(server))
  return True

def DeleteSingleServer(server: Server):
  mongodb.DeleteDocs(collection, 
    {'ServerId': server.ServerId})
  return True

def GetAllServers() -> list[Server]:
  serverList: list[Server] = []
  servs = mongodb.GetManyDocs(collection, {}) or []
  for s in servs:
    serverList.append(Server.from_dict(s))
  return serverList
