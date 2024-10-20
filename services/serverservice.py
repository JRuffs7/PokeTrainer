from dataaccess import serverda, trainerda
from models.Event import Event
from models.enums import EventType
from models.Server import Server
from services import eventservice, pokemonservice


def RegisterServer(serverId: int, channelId: int, serverName: str):
  if serverId is None or channelId is None:
    return None
  
  currServ = GetServer(serverId)
  if currServ:
    currServ.ChannelId = channelId
    currServ.ServerName = serverName
  else:
    currServ = Server.from_dict({
      'ServerId': serverId,
      'ServerName': serverName,
      'ChannelId': channelId,
    })
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
