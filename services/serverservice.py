from dataaccess import serverda
from models.Server import Server


def RegisterServer(serverId, channelId, serverName):
  if serverId is None or channelId is None:
    return None
  serv = Server({
      'ServerId': serverId,
      'ServerName': serverName,
      'ChannelId': channelId,
      'CurrentEventId': None,
  })
  UpsertServer(serv)
  return serv


def GetServer(serverId):
  return serverda.GetServer(serverId)

def GetAllServers():
  return serverda.GetAllServers()

def UpsertServer(server: Server):
  return serverda.UpsertServer(server)


def DeleteServer(server: Server):
  return serverda.DeleteServer(server.ServerId)


def SwapChannel(server: Server, channelId):
  if server.ChannelId == channelId:
    return None
  else:
    server.ChannelId = channelId
    serverda.UpsertServer(server)
    return server