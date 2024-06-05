from dataaccess import serverda, trainerda
from models.Event import Event
from models.enums import EventType
from models.Server import Server
from services import eventservice, pokemonservice


def RegisterServer(serverId, channelId, serverName):
  if serverId is None or channelId is None:
    return None
  serv = Server.from_dict({
      'ServerId': serverId,
      'ServerName': serverName,
      'ChannelId': channelId,
  })
  UpsertServer(serv)
  return serv

#region Data

def GetServer(serverId: int):
  return serverda.GetServer(serverId)

def GetAllServers():
  return serverda.GetAllServers()

def UpsertServer(server: Server):
  return serverda.UpsertServer(server)

def DeleteServer(server: Server):
  return serverda.DeleteServer(server.ServerId)

#endregion

#region Events

def SpecialSpawnEvent(server: Server):
  specialPokemon = pokemonservice.GetSpecialSpawn()
  server.CurrentEvent = Event.from_dict({
    'EventName': f'{pokemonservice.GetPokemonDisplayName(specialPokemon, None, False, False)} Spawn Event',
    'EventType': EventType.SpecialSpawn.value,
  })
  UpsertServer(server)
  return (specialPokemon, trainerda.GetWishlistTrainers(server.ServerId, specialPokemon.Pokemon_Id))

def SpecialBattleEvent(server: Server):
  specialTrainer = eventservice.GetRandomSpecialTrainer()
  server.CurrentEvent = Event.from_dict({
    'EventName': f'{specialTrainer.Name} Battle Event',
    'EventType': EventType.SpecialBattle.value,
  })
  UpsertServer(server)
  return specialTrainer

async def EndEvent(server: Server):
  if not server.CurrentEvent:
    return
  server.CurrentEvent = None
  UpsertServer(server)

#endregion

def SwapChannel(server: Server, channelId):
  if server.ChannelId == channelId:
    return None
  else:
    server.ChannelId = channelId
    serverda.UpsertServer(server)
    return server