from dataaccess import serverda
from models.Event import Event
from models.enums import EventType
from models.Server import Server
from services import pokemonservice


def RegisterServer(serverId, channelId, serverName):
  if serverId is None or channelId is None:
    return None
  serv = Server({
      'ServerId': serverId,
      'ServerName': serverName,
      'ChannelId': channelId,
      'CurrentEvent': None,
  })
  UpsertServer(serv)
  return serv

#region Data

def GetServer(serverId):
  return serverda.GetServer(serverId)

def GetAllServers():
  return serverda.GetAllServers()

def UpsertServer(server: Server):
  return serverda.UpsertServer(server)


def DeleteServer(server: Server):
  return serverda.DeleteServer(server.ServerId)

#endregion

def SpecialSpawnEvent(server: Server):
  specialPokemon = pokemonservice.GetSpecialSpawn()
  server.CurrentEvent = Event({
    'EventName': f'{pokemonservice.GetPokemonDisplayName(specialPokemon, False, False)} Spawn Event',
    'EventType': EventType.SpecialSpawn.value
  })
  UpsertServer(server)
  return specialPokemon


def SwapChannel(server: Server, channelId):
  if server.ChannelId == channelId:
    return None
  else:
    server.ChannelId = channelId
    serverda.UpsertServer(server)
    return server