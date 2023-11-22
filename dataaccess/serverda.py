from threading import Thread

from dataaccess.utility import mongodb
from globals import to_dict
from models.Server import Server

collection: str = 'Server'
serverCache = {}


def GetServer(serverId):
  if serverId in serverCache:
    return serverCache[serverId]
  s = mongodb.GetSingleDoc(collection, {'ServerId': serverId})
  serv = Server(s) if s else None
  if serv:
    serverCache[serverId] = serv
  return serv


def GetAllServers():
  serverList: list[Server] = []
  servs = mongodb.GetManyDocs(collection, {})
  for s in servs if servs else []:
    if s:
      server = Server(s)
      serverCache[server.ServerId] = server
      serverList.append(server)
  return serverList


def UpsertServer(server: Server):
  serverCache[server.ServerId] = server
  thread = Thread(target=PushServerToMongo, args=(server, ))
  thread.start()
  return server


def DeleteServer(serverId):
  del serverCache[serverId]
  thread = Thread(target=DeleteServerFromMongo, args=(serverId, ))
  thread.start()
  return True


def PushServerToMongo(server: Server):
  mongodb.UpsertSingleDoc(collection, {'ServerId': server.ServerId},
                          to_dict(server))
  return


def DeleteServerFromMongo(serverId):
  mongodb.DeleteDocs(collection, {'ServerId': serverId})
  return
