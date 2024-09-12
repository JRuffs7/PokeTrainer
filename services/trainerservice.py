from datetime import UTC, datetime, timedelta
import logging
from random import choice, sample
import uuid
from dataaccess import trainerda
from globals import AdminList, GreatShinyOdds, ShinyOdds, DateFormat, ShortDateFormat, SuperShinyOdds
from models.Egg import TrainerEgg
from models.Item import Pokeball, Potion
from models.Mission import TrainerMission
from models.Shop import SpecialShop
from models.Trainer import Trainer
from models.Pokemon import EvolveData, Pokemon, PokemonData
from services import battleservice, gymservice, itemservice, missionservice, pokemonservice, statservice

captureLog = logging.getLogger('capture')

commandLocks: list[str] = []

#region Data

def CheckTrainer(serverId: int, userId: int):
  return trainerda.CheckTrainer(serverId, userId)

def GetTrainer(serverId: int, userId: int):
  return trainerda.GetSingleTrainer(serverId, userId)

def UpsertTrainer(trainer: Trainer):
  return trainerda.UpsertSingleTrainer(trainer)

def DeleteTrainer(trainer: Trainer):
  return trainerda.DeleteSingleTrainer(trainer)

def StartTrainer(pokemon: PokemonData, serverId: int, userId: int):
  spawn = pokemonservice.GenerateSpawnPokemon(pokemon, level=5)
  trainer = Trainer.from_dict({
    'UserId': userId,
    'ServerId': serverId,
    'Team': [spawn.Id],
    'Pokedex': [pokemon.PokedexId],
    'Health': 50,
    'Money': 500,
    'Pokeballs': { '1': 5, '2': 0, '3': 0, '4': 0 }
  })
  trainer.OwnedPokemon.append(spawn)
  UpsertTrainer(trainer)
  return trainer

def CheckTrainerLock(serverId: int, userId: int):
  return f'{serverId}{userId}' in commandLocks

def TrainerCommandLock(serverId: int, userId: int):
  commandLocks.append(f'{serverId}{userId}')

def TrainerRemoveLock(serverId: int, userId: int):
  commandLocks.remove(f'{serverId}{userId}')

#endregion

#region Inventory/Items

def TryUsePotion(trainer: Trainer, potion: Potion):
  if trainer.Health == 100:
    return 0

  preHealth = trainer.Health
  if potion.HealingAmount == None:
    trainer.Health = 100
  else:
    trainer.Health += potion.HealingAmount
  if trainer.Health > 100:
    trainer.Health = 100
  ModifyItemList(trainer, str(potion.Id), -1)
  trainerda.UpsertSingleTrainer(trainer)
  return trainer.Health - preHealth

def TryDaily(trainer: Trainer, freeMasterball: bool):
  if (not trainer.LastDaily or datetime.strptime(trainer.LastDaily, ShortDateFormat).date() < datetime.now(UTC).date()) or trainer.UserId in AdminList:
    trainer.LastDaily = datetime.now(UTC).strftime(ShortDateFormat)
    trainer.DailyMission = TrainerMission.from_dict({
      'Progress': 0,
      'DayStarted': datetime.now(UTC).strftime(ShortDateFormat),
      'MissionId': missionservice.GetNewDailyMission().Id
    })
    if not trainer.WeeklyMission or (datetime.now(UTC).date()-datetime.strptime(trainer.WeeklyMission.DayStarted, ShortDateFormat).date()).days >= 7:
      trainer.WeeklyMission = TrainerMission.from_dict({
        'Progress': 0,
        'DayStarted': (datetime.now(UTC) - timedelta(days=(datetime.now(UTC).isoweekday()-1))).strftime(ShortDateFormat),
        'MissionId': missionservice.GetNewWeeklyMission().Id
      })

    #Unova Reward
    if HasRegionReward(trainer, 5):
      ModifyItemList(trainer, '4', 20)
      trainer.Money += 500
    else:
      ModifyItemList(trainer, '4', 10)
      trainer.Money += 200
      
    if freeMasterball:
      ModifyItemList(trainer, '1', 1)

    addEgg = TryAddNewEgg(trainer)
    UpsertTrainer(trainer)
    return addEgg
  return -1

def SpecialShopCheck(trainer: Trainer):
  if not trainer.Shop:
    trainer.Shop = SpecialShop({'LastRecycle': datetime.now(UTC).strftime(ShortDateFormat), 'ItemIds': [i.Id for i in sample(itemservice.GetAllItems(), 4)]})
  elif datetime.strptime(trainer.Shop.LastRecycle, ShortDateFormat).date() < datetime.now(UTC).date():
    trainer.Shop.LastRecycle = datetime.now(UTC).strftime(ShortDateFormat)
    trainer.Shop.ItemIds = [i.Id for i in sample(itemservice.GetAllItems(), 4)]
  UpsertTrainer(trainer)

def ModifyItemList(trainer: Trainer, itemId: str, amount: int):
  newAmount = trainer.Items[itemId] + amount if itemId in trainer.Items else amount
  if newAmount < 0:
    newAmount = 0
  trainer.Items.update({ itemId: newAmount })

def HasRegionReward(trainer: Trainer, region: int):
  for b in [b.Id for b in gymservice.GetBadgesByRegion(region)]:
    found = False
    for t in trainer.Badges:
      if t == b:
        found = True
        break
    if not found:
        return False
  return True

def TryAddMissionProgress(trainer: Trainer, action: str, types: list[int], addition: int = 1):
  dailyPass = True
  weeklyPass = True
  #Daily
  if not trainer.DailyMission: #No mission
    dailyPass = False
  else:
    if (datetime.now(UTC).date() - datetime.strptime(trainer.DailyMission.DayStarted, ShortDateFormat).date()).days != 0: #Expired
      dailyPass = False
    dMission = missionservice.GetDailyMission(trainer.DailyMission.MissionId)
    if trainer.DailyMission.Progress >= dMission.Amount: #Completed
      dailyPass = False
    if action.lower() != dMission.Action.lower(): #Wrong Action
      dailyPass = False
    if not missionservice.CheckMissionType(dMission, types): #Invalid Type
      dailyPass = False
  if dailyPass:
    trainer.DailyMission.Progress += addition
    if trainer.DailyMission.Progress >= dMission.Amount:
      trainer.DailyMission.Progress = dMission.Amount
      ModifyItemList(trainer, '50', 3)

  #Weekly
  if not trainer.WeeklyMission: #No mission
    weeklyPass = False
  else:
    if (datetime.now(UTC).date() - datetime.strptime(trainer.WeeklyMission.DayStarted, ShortDateFormat).date()).days >= 7: #Expired
      weeklyPass = False
    wMission = missionservice.GetWeeklyMission(trainer.WeeklyMission.MissionId)
    if trainer.WeeklyMission.Progress >= wMission.Amount: #Completed
      weeklyPass = False
    if action.lower() != wMission.Action.lower(): #Wrong action
      weeklyPass = False
  if weeklyPass:
    trainer.WeeklyMission.Progress += addition
    if trainer.WeeklyMission.Progress >= wMission.Amount:
      trainer.WeeklyMission.Progress = wMission.Amount
      ModifyItemList(trainer, '1', 1)

def GetTrainerItemList(trainer: Trainer, itemType: int | None = None):
  if itemType == 0: #Pokeball
    return [itemservice.GetPokeball(i) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(p.Id) for p in itemservice.GetAllPokeballs()]]
  if itemType == 1: #Potions
    return [itemservice.GetPotion(i) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(p.Id) for p in itemservice.GetAllPotions()]]
  if itemType == 2: #Candy
    return [itemservice.GetCandy(i) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(c.Id) for c in itemservice.GetAllCandies()]]
  if itemType == 3: #EvoItems
    return [itemservice.GetEvoItem(i) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(e.Id) for e in itemservice.GetAllEvoItems()]]
  return [itemservice.GetItem(i) for i in trainer.Items if trainer.Items[i] > 0]

#endregion

#region Eggs

def TryAddNewEgg(trainer: Trainer):
  #Galar Reward
  if(len(trainer.Eggs) < (8 if HasRegionReward(trainer, 8) else 5)):
    randId = choice(range(1, 101))

    #Johta Reward
    if HasRegionReward(trainer, 2):
      newEggId = 1 if randId <= 50 else 2 if randId <= 90 else 3
    else:
      newEggId = 1 if randId <= 65 else 2 if randId <= 95 else 3

    trainer.Eggs.append(TrainerEgg.from_dict({
      'Id': uuid.uuid4().hex,
      'EggId': newEggId
    }))
    return newEggId
  return 0

def EggInteraction(trainer: Trainer):
  updated = False
  for egg in trainer.Eggs:
    if egg.SpawnCount < itemservice.GetEgg(egg.EggId).SpawnsNeeded:
      egg.SpawnCount += 1
      updated = True
  
  if updated:
    UpsertTrainer(trainer)

def CanEggHatch(egg: TrainerEgg):
  return egg.SpawnCount == itemservice.GetEgg(egg.EggId).SpawnsNeeded

def TryHatchEgg(trainer: Trainer, eggId: str):
  egg = next(e for e in trainer.Eggs if e.Id == eggId)
  eggData = itemservice.GetEgg(egg.EggId)
  if egg.SpawnCount < eggData.SpawnsNeeded:
    return None

  trainer.Eggs = [e for e in trainer.Eggs if e.Id != eggId]
  pkmn = choice(pokemonservice.GetPokemonByRarity(eggData.Hatch))
  while pkmn.EvolvesInto and pkmn.Rarity == 3:
    pkmn = choice(pokemonservice.GetPokemonByRarity(eggData.Hatch))
  newPokemon = pokemonservice.GenerateSpawnPokemon(pkmn, GetShinyOdds(trainer), 1)
  if not newPokemon.IsShiny:
    newPokemon.IsShiny = choice(range(0, GetShinyOdds(trainer))) == int(GetShinyOdds(trainer)/2)
  trainer.OwnedPokemon.append(newPokemon)
  trainer.Money += 50
  TryAddToPokedex(trainer, pkmn, newPokemon.IsShiny)
  if len(trainer.Team) < 6:
    trainer.Team.append(newPokemon.Id)
  UpsertTrainer(trainer)
  return newPokemon.Id

#endregion

#region Pokedex

def GetPokedexList(trainer: Trainer, orderString: str, shiny: int|None, pokemonID: int|None, type: int|None, legendary: int|None, gender: int):
  pokemonList = [p for p in trainer.OwnedPokemon]
  if pokemonID:
    pokemonList = [p for p in pokemonList if p.Pokemon_Id == pokemonID]
  if shiny == 1:
    pokemonList = [p for p in pokemonList if p.IsShiny]
  if gender:
    pokemonList = [p for p in pokemonList if p.IsFemale is not None and (p.IsFemale if gender == 1 else not p.IsFemale)]

  pkmnDataList = pokemonservice.GetPokemonByIdList([p.Pokemon_Id for p in pokemonList])
  if type:
    pkmnDataList = [p for p in pkmnDataList if type in p.Types]
  if legendary:
    pkmnDataList = [p for p in pkmnDataList if ((p.IsLegendary or p.IsMythical or p.IsUltraBeast) if legendary == 1 else not (p.IsLegendary or p.IsMythical or p.IsUltraBeast))]
  pokemonList = [p for p in pokemonList if p.Pokemon_Id in [po.Id for po in pkmnDataList]]

  match orderString:
    case "height":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,x.Height))
      else:
        pokemonList.sort(key=lambda x: x.Height)
    case "dex":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,next(p for p in pkmnDataList if p.Id == x.Pokemon_Id).PokedexId,x.Pokemon_Id))
      else:
        pokemonList.sort(key=lambda x: (next(p for p in pkmnDataList if p.Id == x.Pokemon_Id).PokedexId,x.Pokemon_Id))
    case "name":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,(x.Nickname if x.Nickname else next(p for p in pkmnDataList if p.Id == x.Pokemon_Id).Name)))
      else:
        pokemonList.sort(key=lambda x: (x.Nickname if x.Nickname else next(p for p in pkmnDataList if p.Id == x.Pokemon_Id).Name))
    case "weight":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,x.Weight))
      else:
        pokemonList.sort(key=lambda x: x.Weight)
    case "level":
      if shiny == 2:
        pokemonList.sort(key=lambda x: (-x.IsShiny,-x.Level,x.Pokemon_Id))
      else:
        pokemonList.sort(key=lambda x: (-x.Level,x.Pokemon_Id))
    case _:
      if shiny == 2:
        pokemonList.sort(key=lambda x: -x.IsShiny)
  return pokemonList

def TryAddToPokedex(trainer: Trainer, data: PokemonData, shiny: bool):
  if data.PokedexId not in trainer.Pokedex:
    trainer.Pokedex.append(data.PokedexId)
  if data.Id not in trainer.Formdex:
    trainer.Formdex.append(data.Id)
  if shiny and data.Id not in trainer.Shinydex:
    trainer.Shinydex.append(data.Id)

def Evolve(trainer: Trainer, initialPkmn: Pokemon, initialData: PokemonData, evolveMon: EvolveData):
  newData = pokemonservice.GetPokemonById(evolveMon.EvolveID)
  newPkmn = pokemonservice.EvolvePokemon(initialPkmn, initialData, newData)
  index = trainer.OwnedPokemon.index(initialPkmn)
  trainer.OwnedPokemon[index] = newPkmn
  if evolveMon.ItemNeeded:
    ModifyItemList(trainer, str(evolveMon.ItemNeeded), -1)
  TryAddToPokedex(trainer, newData, newPkmn.IsShiny)
  TryAddMissionProgress(trainer, 'Evolve', [])
  if newData.PokedexId == 869 and initialPkmn.IsShiny:
    for p in pokemonservice.GetPokemonByPokedexId(869):
      if p.Id not in trainer.Shinydex:
        trainer.Shinydex.append(p.Id)
  UpsertTrainer(trainer)
  return newPkmn

def ReleasePokemon(trainer: Trainer, pokemonIds: list[str]):
  released = next(p for p in trainer.OwnedPokemon if p.Id in pokemonIds)
  trainer.OwnedPokemon = [p for p in trainer.OwnedPokemon if p.Id not in pokemonIds]
  TryAddMissionProgress(trainer, 'Release', [], len(pokemonIds))
  UpsertTrainer(trainer)
  return pokemonservice.GetPokemonById(released.Pokemon_Id).Name

def TradePokemon(trainerOne: Trainer, pokemonOne: Pokemon, trainerTwo: Trainer, pokemonTwo: Pokemon):
  trainerOne.OwnedPokemon = [p for p in trainerOne.OwnedPokemon if p.Id != pokemonOne.Id]
  trainerTwo.OwnedPokemon = [p for p in trainerTwo.OwnedPokemon if p.Id != pokemonTwo.Id]
  trainerOne.OwnedPokemon.append(pokemonTwo)
  TryAddToPokedex(trainerOne, pokemonservice.GetPokemonById(pokemonTwo.Pokemon_Id), pokemonTwo.IsShiny)
  TryAddMissionProgress(trainerOne, 'Trade', [])
  UpsertTrainer(trainerOne)
  trainerTwo.OwnedPokemon.append(pokemonOne)
  TryAddToPokedex(trainerTwo, pokemonservice.GetPokemonById(pokemonOne.Pokemon_Id), pokemonOne.IsShiny)
  TryAddMissionProgress(trainerTwo, 'Trade', [])
  UpsertTrainer(trainerTwo)

#endregion

#region Team

def GetTeam(trainer: Trainer):
  return [next(p for p in trainer.OwnedPokemon if p.Id == pokeId) for pokeId in trainer.Team]

def SetTeamSlot(trainer: Trainer, slotNum: int, pokemonId: str):
  #swapping
  if pokemonId in trainer.Team:
    currentSlot = trainer.Team.index(pokemonId)
    currentPkmn = trainer.Team[slotNum]
    trainer.Team[currentSlot] = currentPkmn
    trainer.Team[slotNum] = pokemonId
  #adding
  elif slotNum == len(trainer.Team):
    trainer.Team.append(pokemonId)
  #replacing
  else:
    trainer.Team[slotNum] = pokemonId
  UpsertTrainer(trainer)

#endregion

#region Spawn

def TryCapture(pokeball: Pokeball, trainer: Trainer, spawn: Pokemon):
  caught = False
  pokemon = pokemonservice.GetPokemonById(spawn.Pokemon_Id)
  ModifyItemList(trainer, str(pokeball.Id), -1)

  #Sinnoh Reward
  if (HasRegionReward(trainer, 4) and choice(range(1, 101)) < 6) or pokemonservice.CaptureSuccess(pokeball, pokemon, spawn.Level):
    trainer.OwnedPokemon.append(spawn)
    TryAddToPokedex(trainer, pokemon, spawn.IsShiny)
    TryAddMissionProgress(trainer, 'Catch', pokemon.Types)
    #Paldea Reward
    if HasRegionReward(trainer, 9):
      exp = spawn.Level
      team = GetTeam(trainer)
      teamData = pokemonservice.GetPokemonByIdList([t.Pokemon_Id for t in team])
      for p in team:
        pokemonservice.AddExperience(
          p, 
          next(t for t in teamData if t.Id == p.Pokemon_Id), 
          exp)
    if len(trainer.Team) < 6:
      trainer.Team.append(spawn.Id)
    caught = True
  else:
    trainer.Health -= (5-pokeball.Id)
    trainer.Health = 0 if trainer.Health < 0 else trainer.Health
  UpsertTrainer(trainer)
  return caught

def TryWildFight(trainer: Trainer, trainerPkmnData: PokemonData, wild: Pokemon, wildData: PokemonData):
    trainerPokemon = next(p for p in trainer.OwnedPokemon if p.Id == trainer.Team[0])
    healthLost = battleservice.WildFight(trainerPkmnData, wildData, trainerPokemon.Level, wild.Level)

    #Hoenn Reward
    if HasRegionReward(trainer, 3) and choice(range(1, 101)) < 11:
      healthLost = 0
      
    trainer.Health -= healthLost
    trainer.Health = 0 if trainer.Health < 0 else trainer.Health
    if healthLost < 10 and trainer.Health > 0:
      exp = wildData.Rarity*wild.Level*2 if wildData.Rarity <= 2 else wildData.Rarity*wild.Level
      pokemonservice.AddExperience(
        trainerPokemon, 
        trainerPkmnData, 
        exp)
      trainer.Money += 25
      TryAddMissionProgress(trainer, 'Fight', wildData.Types)
      #Kanto Reward
      if HasRegionReward(trainer, 1) and len(trainer.Team) > 1:
        teamMember = next(p for p in trainer.OwnedPokemon if p.Id == trainer.Team[1])
        pkmn = pokemonservice.GetPokemonById(teamMember.Pokemon_Id)
        pokemonservice.AddExperience(
          teamMember, 
          pkmn, 
          int(exp/2))

    candy = itemservice.TryGetCandy() if healthLost < 10 else None
    if candy:
      ModifyItemList(trainer.Items, str(candy.Id), 1)
    
    UpsertTrainer(trainer)
    return (healthLost,candy)

def TryAddWishlist(trainer: Trainer, pokemonId: int):
  if pokemonId in trainer.Wishlist:
    return False
  trainer.Wishlist.append(pokemonId)
  UpsertTrainer(trainer)
  return True

def GetShinyOdds(trainer: Trainer):
  totalPkmn = pokemonservice.GetAllPokemon()
  totalPkdx = len(set(p.PokedexId for p in totalPkmn))
  if HasRegionReward(trainer, 1000) and len(trainer.Pokedex) == totalPkdx:
    return SuperShinyOdds
  elif HasRegionReward(trainer, 1000) or len(trainer.Pokedex) == totalPkdx:
    return GreatShinyOdds
  return ShinyOdds

#endregion