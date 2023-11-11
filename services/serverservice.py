from dataaccess import serverda
from models.Server import Server


def StartServer(serverId, channelId, serverName, chance, deletePrev):
  if serverId is None or channelId is None:
    return None
  serv = Server({
      'ServerId': serverId,
      'ChannelIds': [channelId],
      'ServerName': serverName,
      'SpawnChance': chance,
      'DeletePrevious': 1 if deletePrev else 0
  })
  serverda.UpsertServer(serv)
  return serv


def GetServer(serverId):
  return serverda.GetServer(serverId)


def GetServers():
  return serverda.GetAllServers()


def UpsertServer(server: Server):
  return serverda.UpsertServer(server)


def DeleteServer(server: Server):
  return serverda.DeleteServer(server.ServerId)


def ToggleChannel(server: Server, channelId):
  added = True
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

def ChangePercent(server: Server, percent):
  server.SpawnChance = percent
  UpsertServer(server)
  
def ToggleDeleteSpawn(server: Server):
  server.DeletePrevious = 0 if server.DeletePrevious else 1
  UpsertServer(server)
  return server.DeletePrevious