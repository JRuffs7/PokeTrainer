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

def GetServer(serverId: int):
  return serverda.GetSingleServer(serverId)

def GetAllServers():
  return serverda.GetServers()

def UpsertServer(server: Server):
  return serverda.UpsertSingleServer(server)

def DeleteServer(server: Server):
  return serverda.DeleteSingleServer(server)

#endregion

#region Events

def SpecialSpawnEvent(server: Server):
  specialPokemon = pokemonservice.GetSpecialSpawn()
  server.CurrentEvent = Event.from_dict({
    'EventName': f'{pokemonservice.GetPokemonDisplayName(specialPokemon, None, False, False)} Spawn Event',
    'EventType': EventType.SpecialSpawn.value,
  })
  UpsertServer(server)
  return (specialPokemon, [t.UserId for t in trainerda.GetTrainers(server.ServerId) if specialPokemon.Pokemon_Id in t.Wishlist])

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
    serverda.UpsertSingleServer(server)
    return server