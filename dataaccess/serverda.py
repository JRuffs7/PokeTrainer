from threading import Thread

from dataaccess.utility import mongodb, sqliteda
from globals import to_dict
from models.Server import Server

collection: str = 'Server'

def GetServer(serverId: int) -> Server|None:
  serv = sqliteda.Load('Server', serverId)
  if not serv:
    s = mongodb.GetSingleDoc(collection, {'ServerId': serverId})
    serv = Server(s) if s else None
    if serv:
      sqliteda.Save('Server', serverId, serv)
  return serv


def GetAllServers() -> list[Server]:
  serverList: list[Server] = []
  servs = mongodb.GetManyDocs(collection, {})
  for s in servs if servs else []:
    if s:
      server = Server(s)
      sqliteda.Save('Server', server.ServerId, server)
      serverList.append(server)
  return serverList


def UpsertServer(server: Server) -> Server:
  sqliteda.Save('Server', server.ServerId, server)
  thread = Thread(target=PushServerToMongo, args=(server, ))
  thread.start()
  return server


def DeleteServer(serverId: int):
  sqliteda.Remove('Server', serverId)
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
