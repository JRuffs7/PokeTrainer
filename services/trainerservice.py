from datetime import UTC, datetime, timedelta
from random import choice
import uuid
from dataaccess import trainerda
from globals import AdminList, DateFormat, GreatShinyOdds, ShinyOdds, ShortDateFormat, SuperShinyOdds
from models.Egg import TrainerEgg
from models.Mission import TrainerMission
from models.Trainer import Trainer
from models.Pokemon import EvolveData, Pokemon, PokemonData
from services import gymservice, itemservice, missionservice, pokemonservice, statservice

#region Data

def CheckTrainer(serverId: int, userId: int):
  return trainerda.CheckTrainer(serverId, userId)

def GetTrainer(serverId: int, userId: int):
  return trainerda.GetSingleTrainer(serverId, userId)

def GetAllTrainers():
  return trainerda.GetManyTrainers()

def UpsertTrainer(trainer: Trainer):
  trainer.LastUpdated = datetime.now(UTC).strftime(DateFormat)
  return trainerda.UpsertSingleTrainer(trainer)

def DeleteTrainer(trainer: Trainer):
  return trainerda.DeleteSingleTrainer(trainer)

def StartTrainer(pokemon: PokemonData, serverId: int, userId: int):
  spawn = pokemonservice.GenerateSpawnPokemon(pokemon, 5)
  trainer = Trainer.from_dict({
    'UserId': userId,
    'ServerId': serverId,
    'Team': [spawn.Id],
    'Region': pokemon.Generation,
    'Pokedex': [pokemon.PokedexId],
    'Money': 500,
    'Items': { '4': 5 }
  })
  trainer.OwnedPokemon.append(spawn)
  TryAddToPokedex(trainer, pokemon, spawn.IsShiny)
  UpsertTrainer(trainer)
  return trainer

def ChangeRegion(trainer: Trainer, region: int, pokemon: PokemonData|None):
  if pokemon:
    newStarter = pokemonservice.GenerateSpawnPokemon(pokemon, 5, GetShinyOdds(trainer))
    trainer.OwnedPokemon.append(newStarter)
    trainer.Team = [newStarter.Id]
    TryAddToPokedex(trainer, pokemon, newStarter.IsShiny)
    trainer.Money += 500
    ModifyItemList(trainer, '4', 5)
  trainer.Region = region
  UpsertTrainer(trainer)
  return trainer

#endregion

#region Completion

def RegionCompleted(trainer: Trainer, region: int):
  if region != 1000 and region not in trainer.EliteFour:
    return False
  if [g for g in gymservice.GetBadgesByRegion(region) if g.Id not in trainer.Badges]:
    return False
  regionDex = pokemonservice.GetPokemonByRegion(region)
  if [p for p in regionDex if p.Id not in trainer.Formdex]:
    return False
  return True

def RegionsVisited(trainer: Trainer):
  badges = gymservice.GetAllBadges()
  allStarters = pokemonservice.GetStarterPokemon()
  visited: list[int] = []
  for region in [g for g in gymservice.GetRegions() if g < 1000]:
    starters = [s for s in allStarters if s.Generation == region]
    if [s for s in starters if s.PokedexId in trainer.Pokedex] and (region not in visited):
      visited.append(region)
    if [b for b in badges if b.Generation == region and b.Id in trainer.Badges] and (region not in visited):
      visited.append(region)
  return visited

def ChangeRegions(trainer: Trainer):
  allRegions = gymservice.GetRegions()
  badges = gymservice.GetAllBadges()
  allStarters = pokemonservice.GetStarterPokemon()
  available: list[int] = []
  for region in allRegions:
    starters = [s for s in allStarters if s.Generation == region]
    if [s for s in starters if s.PokedexId in trainer.Pokedex] and (region not in available):
      available.append(region)
    if [b for b in badges if b.Generation == region and b.Id in trainer.Badges] and (region not in available):
      available.append(region)
  if 1000 not in available and len(trainer.EliteFour) == [r for r in allRegions if r < 1000]:
    available.append(1000)
  return available

def ResetTrainer(trainer: Trainer, starter: PokemonData, keepShiny: bool):
  shinyPkmn = [p for p in trainer.OwnedPokemon if p.IsShiny] if keepShiny else []
  DeleteTrainer(trainer)
  for s in shinyPkmn:
    nic = s.Nickname
    fem = s.IsFemale
    hei = s.Height
    wei = s.Weight
    cau = s.CaughtBy
    s = pokemonservice.GenerateSpawnPokemon(pokemonservice.GetInitialStage(s.Pokemon_Id), 1)
    s.IsShiny = True
    s.Nickname = nic
    s.IsFemale = fem
    s.Height = hei
    s.Weight = wei
    s.CaughtBy = cau
  newTrainer = StartTrainer(starter, trainer.ServerId, trainer.UserId)
  newTrainer.OwnedPokemon.extend(shinyPkmn)
  UpsertTrainer(newTrainer)
  return newTrainer

def HasRegionReward(trainer: Trainer, region: int):
  return (region in trainer.EliteFour) and (len([b for b in gymservice.GetBadgesByRegion(region) if b.Id not in trainer.Badges]) == 0)

#endregion

#region Inventory/Items

def CanUseDaily(trainer: Trainer):
  return (not trainer.LastDaily) or (datetime.strptime(trainer.LastDaily, ShortDateFormat).date() < datetime.now(UTC).date()) or (trainer.UserId in AdminList)

def TryDaily(trainer: Trainer, freeMasterball: bool):
  if CanUseDaily(trainer):
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
    ModifyItemList(trainer, '3' if HasRegionReward(trainer, 5) else '4', 10)
    trainer.Money += 200
      
    if freeMasterball:
      ModifyItemList(trainer, '1', 1)
    UpsertTrainer(trainer)
    return True
  return False

def ModifyItemList(trainer: Trainer, itemId: str, amount: int):
  newAmount = max(trainer.Items[itemId] + amount, 0) if itemId in trainer.Items else max(amount, 0)
  trainer.Items.update({ itemId: newAmount })
  
def ModifyTMList(trainer: Trainer, moveId: str, amount: int):
  newAmount = max(trainer.TMs[moveId] + amount, 0) if moveId in trainer.TMs else max(amount, 0)
  trainer.TMs.update({ moveId: newAmount })

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
    return [itemservice.GetPokeball(int(i)) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(p.Id) for p in itemservice.GetAllPokeballs()]]
  if itemType == 1: #Potions
    return [itemservice.GetPotion(int(i)) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(p.Id) for p in itemservice.GetAllPotions()]]
  if itemType == 2: #Candy
    return [itemservice.GetCandy(int(i)) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(c.Id) for c in itemservice.GetAllCandies()]]
  if itemType == 3: #EvoItems
    return [itemservice.GetEvoItem(int(i)) for i in trainer.Items if trainer.Items[i] > 0 and i in [str(e.Id) for e in itemservice.GetAllEvoItems()]]
  return [itemservice.GetItem(int(i)) for i in trainer.Items if trainer.Items[i] > 0]

def UpvoteReward(userId: int):
  trainers = trainerda.GetUserTrainers(userId)
  for trainer in trainers:
    ModifyItemList(trainer, '50', 5)
    UpsertTrainer(trainer)

#endregion

#region Eggs

def CheckDaycareForEgg(trainer: Trainer):
  daycareMon = GetDaycare(trainer)
  #Only 1 Pokemon
  if (len(daycareMon) < 2):
    return None
  #Eggs full
  if len(trainer.Eggs) >= (8 if HasRegionReward(trainer, 6) else 5):
    return None
  minTime = (720 if HasRegionReward(trainer, 8) else 360)
  lastEggTime = datetime.strptime(trainer.LastDaycareEgg, DateFormat).replace(tzinfo=UTC) if trainer.LastDaycareEgg else None
  #Not enough time
  #Galar Reward
  if lastEggTime and int((datetime.now(UTC) - lastEggTime).total_seconds()//60) < minTime:
    return None
  for p in trainer.Daycare:
    timeAdded = datetime.strptime(trainer.Daycare[p], DateFormat).replace(tzinfo=UTC)
    if int((datetime.now(UTC) - timeAdded).total_seconds()//60) < minTime:
      return None
  #Null gender
  if (daycareMon[0].IsFemale == None and daycareMon[0].Pokemon_Id != 132) or (daycareMon[1].IsFemale == None and daycareMon[1].Pokemon_Id != 132):
    return None
  #Same gender
  if daycareMon[0].IsFemale == daycareMon[1].IsFemale:
    return False
  #Both ditto
  if daycareMon[0].Pokemon_Id == 132 and daycareMon[1].Pokemon_Id == 132:
    return None
  data = [pokemonservice.GetPokemonById(p.Pokemon_Id) for p in daycareMon]
  #Unbreedable
  if 15 in data[0].EggGroups+data[1].EggGroups:
    return None
  commonEggGroups = [e for e in data[0].EggGroups if e in data[1].EggGroups]
  #No common group and no ditto
  if not commonEggGroups and 13 not in data[0].EggGroups+data[1].EggGroups:
    return None
  mother = next(p for p in daycareMon if p.IsFemale) if 132 not in [p.Pokemon_Id for p in daycareMon] else next(p for p in daycareMon if p.Pokemon_Id != 132)
  father = next(p for p in daycareMon if p.Id != mother.Id)
  ivs = {}
  while len(ivs) < 3:
    stat = choice([s.Id for s in statservice.GetAllStats() if s.Id < 7 and str(s.Id) not in ivs])
    inherit = choice([mother,father])
    ivs[str(stat)] = inherit.IVs[str(stat)]
  offspring = pokemonservice.GetInitialStage(mother.Pokemon_Id)
  species = pokemonservice.GetPokemonByPokedexId(offspring.PokedexId)
  if len(species) > 1 and next((s for s in species if s.Generation == trainer.Region),None):
    offspring = next(s for s in species if s.Generation == trainer.Region)
  newEgg = TrainerEgg.from_dict({
    'Id': uuid.uuid4().hex,
    'Generation': offspring.Generation,
    'OffspringId': offspring.Id,
    'SpawnsNeeded': offspring.HatchCount,
    'ShinyOdds': int(GetShinyOdds(trainer)/(2 if mother.OriginalTrainer != father.OriginalTrainer else 1)),
    'IVs': ivs
  })
  trainer.Eggs.append(newEgg)
  trainer.LastDaycareEgg = datetime.now(UTC).strftime(DateFormat)
  UpsertTrainer(trainer)
  return newEgg

def EggInteraction(trainer: Trainer):
  updated = False
  for egg in trainer.Eggs:
    if egg.SpawnCount < egg.SpawnsNeeded:
      egg.SpawnCount += 1
      updated = True
  
  if updated:
    UpsertTrainer(trainer)

def TryHatchEgg(trainer: Trainer, egg: TrainerEgg):
  if egg.SpawnCount < egg.SpawnsNeeded:
    return None

  trainer.Eggs = [e for e in trainer.Eggs if e.Id != egg.Id]
  pkmn = pokemonservice.GetPokemonById(egg.OffspringId)
  newPokemon = pokemonservice.GenerateSpawnPokemon(pkmn, 1, egg.ShinyOdds)
  trainer.OwnedPokemon.append(newPokemon)
  trainer.Money += 100
  TryAddToPokedex(trainer, pkmn, newPokemon.IsShiny)
  if len(trainer.Team) < 6:
    trainer.Team.append(newPokemon.Id)
  return newPokemon

#endregion

#region Pokedex

def GetMyPokemon(trainer: Trainer, orderString: str|None, shiny: int|None, pokemonID: int|None, type: int|None, legendary: int|None, gender: int|None):
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
    pkmnDataList = [p for p in pkmnDataList if (pokemonservice.IsLegendaryPokemon(p) if legendary == 1 else not pokemonservice.IsLegendaryPokemon(p))]
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

def Evolve(trainer: Trainer, initialPkmn: Pokemon, initialData: PokemonData, evolveMon: EvolveData, combine: Pokemon|None):
  newData = pokemonservice.GetPokemonById(evolveMon.EvolveID)
  newPkmn = pokemonservice.EvolvePokemon(initialPkmn, initialData, newData)
  index = trainer.OwnedPokemon.index(initialPkmn)
  trainer.OwnedPokemon[index] = newPkmn
  if evolveMon.ItemNeeded:
    ModifyItemList(trainer, str(evolveMon.ItemNeeded), -1)
  if evolveMon.PokemonNeeded:
    trainer.OwnedPokemon.remove(combine)
  TryAddToPokedex(trainer, newData, newPkmn.IsShiny)
  TryAddMissionProgress(trainer, 'Evolve', [])
  if newData.PokedexId == 869 and initialPkmn.IsShiny:
    for p in pokemonservice.GetPokemonByPokedexId(869):
      if p.Id not in trainer.Shinydex:
        trainer.Shinydex.append(p.Id)
  
  if initialPkmn.Pokemon_Id == 290 and len(trainer.Team) < 6: #Nincada
    shedinja = pokemonservice.GetPokemonById(292)
    shedinjaSpawn = pokemonservice.GenerateSpawnPokemon(shedinja, 1, GetShinyOdds(trainer))
    trainer.Team.append(shedinjaSpawn.Id)
    TryAddToPokedex(trainer, shedinja, shedinjaSpawn.IsShiny)

  UpsertTrainer(trainer)
  return newPkmn

def ReleasePokemon(trainer: Trainer, pokemonIds: list[str]):
  trainer.OwnedPokemon = [p for p in trainer.OwnedPokemon if p.Id not in pokemonIds]
  TryAddMissionProgress(trainer, 'Release', [], len(pokemonIds))

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

def GetDaycare(trainer: Trainer):
  return [next(p for p in trainer.OwnedPokemon if p.Id == pokeId) for pokeId in trainer.Daycare]

def SetTeamSlot(trainer: Trainer, slotNum: int, pokemonId: str):
  #swapping
  if pokemonId in trainer.Team:
    currentSlot = trainer.Team.index(pokemonId)
    currentPkmn = trainer.Team[slotNum]
    trainer.Team[currentSlot] = currentPkmn
    trainer.Team[slotNum] = pokemonId
  #replacing
  else:
    trainer.Team[slotNum] = pokemonId

#endregion

#region Spawn

def GetShinyOdds(trainer: Trainer):
  totalPkmn = pokemonservice.GetAllPokemon()
  totalPkdx = len(set(p.PokedexId for p in totalPkmn))
  #Voltage Reward
  if HasRegionReward(trainer, 1000) and len(trainer.Pokedex) == totalPkdx:
    return SuperShinyOdds
  elif HasRegionReward(trainer, 1000) or len(trainer.Pokedex) == totalPkdx:
    return GreatShinyOdds
  return ShinyOdds

#endregion