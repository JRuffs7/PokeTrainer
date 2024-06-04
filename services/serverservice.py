from dataaccess import serverda, trainerda
from models.Event import Event
from models.enums import EventType, StatCompare
from models.Server import Server
from services import eventservice, pokemonservice, trainerservice
from services.utility import discordservice_server


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

def StatCompareEvent(server: Server):
  comparison = eventservice.GetRandomStatCompare()
  server.CurrentEvent = Event.from_dict({
    'EventName': f'{comparison.name} Comparison Event',
    'EventType': EventType.StatCompare.value,
    'SubType': comparison.value,
  })
  UpsertServer(server)

def PokemonCountEvent(server: Server):
  count = eventservice.GetRandomCount()
  server.CurrentEvent = Event.from_dict({
    'EventName': f'{count.name} Count Event',
    'EventType': EventType.PokemonCount.value,
    'SubType': count.value,
  })
  UpsertServer(server)

async def EndEvent(server: Server):
  if not server.CurrentEvent:
    return
  winners: list[tuple[int,int]] = []
  if server.CurrentEvent.EventEntries:
    match(server.CurrentEvent.EventType):
      case EventType.PokemonCount.value:
        entryList = {k: float(v) for k, v in sorted(server.CurrentEvent.EventEntries.items(), key=lambda item: -float(item[1]))}
        winners = eventservice.TopThreeWinners(entryList, False)
      case EventType.StatCompare.value:
        smallerComp = server.CurrentEvent.SubType == StatCompare.Lightest.value or server.CurrentEvent.SubType == StatCompare.Shortest.value
        if smallerComp:
          entryList = {k: float(v) for k, v in sorted(server.CurrentEvent.EventEntries.items(), key=lambda item: float(item[1]))}
        else:
          entryList = {k: float(v) for k, v in sorted(server.CurrentEvent.EventEntries.items(), key=lambda item: -float(item[1]))}
        winners = eventservice.TopThreeWinners(entryList, smallerComp)
      case _:
        pass

  for tup in winners:
    trainerservice.EventWinner(trainerservice.GetTrainer(server.ServerId, tup[0]), tup[1])

  try:
    await discordservice_server.PrintEventWinners(server, winners)
    server.CurrentEvent = None
    UpsertServer(server)
  except:
    DeleteServer(server)

#endregion

def SwapChannel(server: Server, channelId):
  if server.ChannelId == channelId:
    return None
  else:
    server.ChannelId = channelId
    serverda.UpsertServer(server)
    return server