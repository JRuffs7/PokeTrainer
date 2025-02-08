from dataaccess import serverda
from models.Server import Server


def RegisterServer(serverId: int, channelId: int):
  if serverId is None or channelId is None:
    return None
  currServ = GetServer(serverId)
  currServ.ChannelId = channelId
  UpsertServer(currServ)
  return currServ

#region Data

def CheckServer(serverId: int):
  return serverda.CheckServer(serverId)

def GetServer(serverId: int):
  return serverda.GetSingleServer(serverId)

def GetAllServers():
  return serverda.GetAllServers()

def UpsertServer(server: Server):
  return serverda.UpsertSingleServer(server)

def DeleteServer(server: Server):
  return serverda.DeleteSingleServer(server)

#endregion
