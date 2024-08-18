from threading import Thread

from dataaccess.utility import mongodb, sqliteda
from globals import to_dict
from models.Server import Server

collection: str = 'Server'

def GetServer(serverId: int) -> Server|None:
  serv = sqliteda.Load(collection, serverId)
  if not serv:
    s = mongodb.GetSingleDoc(collection, {'ServerId': serverId})
    serv = Server.from_dict(s) if s else None
    if serv:
      sqliteda.Save(collection, serverId, serv)
  return serv


def GetAllServers() -> list[Server]:
  serverList: list[Server] = []
  servs = mongodb.GetManyDocs(collection, {}, {'_id':0})
  for s in servs if servs else []:
    if s:
      server = Server.from_dict(s)
      sqliteda.Save(collection, server.ServerId, server)
      serverList.append(server)
  return serverList


def UpsertServer(server: Server) -> Server:
  sqliteda.Save(collection, server.ServerId, server)
  thread = Thread(target=PushServerToMongo, args=(server, ))
  thread.start()
  return server


def DeleteServer(serverId: int):
  sqliteda.Remove(collection, serverId)
  thread = Thread(target=DeleteServerFromMongo, args=(serverId, ))
  thread.start()
  return


def PushServerToMongo(server: Server):
  mongodb.UpsertSingleDoc(collection, {'ServerId': server.ServerId},
                          to_dict(server))
  return


def DeleteServerFromMongo(serverId):
  mongodb.DeleteDocs(collection, {'ServerId': serverId})
  return
