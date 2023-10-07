from dataaccess import serverda
from models.CustomException import ServerInvalidException
from models.Server import Server


def StartServer(serverId, channelId, serverName, chance):
  if serverId is None or channelId is None:
    return None
  serv = Server({
      'ServerId': serverId,
      'ChannelIds': [channelId],
      'ServerName': serverName,
      'SpawnChance': chance,
  })
  serverda.UpsertServer(serv)
  return serv


def GetServer(serverId):
  return serverda.GetServer(serverId)


def GetServers():
  return serverda.GetAllServers()


def UpsertServer(server):
  return serverda.UpsertServer(server)


def DeleteServer(serverId):
  serv = GetServer(serverId)
  if not serv:
    raise ServerInvalidException
  return serverda.DeleteServer(serverId)


def ToggleChannel(serverId, channelId):
  server = serverda.GetServer(serverId)
  added = True
  if not server:
    raise ServerInvalidException

  if not server.ChannelIds.__contains__(channelId):
    server.ChannelIds.append(channelId)
  else:
    if len(server.ChannelIds) > 1:
      added = False
      server.ChannelIds.remove(channelId)
    else:
      return None
  serverda.UpsertServer(server)
  return added
