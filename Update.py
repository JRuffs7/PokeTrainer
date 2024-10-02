import os
from random import choice
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from dataaccess import serverda, trainerda
from models.Server import Server
from models.Stat import StatEnum
from models.Trainer import Trainer
from services import moveservice, pokemonservice, statservice

def GetManyDocs(collection, filters, fields):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      return list(coll.find(filters, fields))
  except Exception:
    return []

def UpdateServers():
	updateList: list[Server] = []
	for s in GetManyDocs('Server', {}, {'_id':0}):
		try:
			newServer = Server.from_dict({
				'ServerName': s['ServerName'] if 'ServerName' in s else '',
				'ServerId': s['ServerId'] if 'ServerId' in s else '',
				'ChannelId': s['ChannelId'] if 'ChannelId' in s else '',
				'CurrentEvent': None
			})
			updateList.append(newServer)
		except Exception:
			print(f'Server failed to update: {s["ServerId"]}-{s["ServerName"]}')
			pass
	return updateList
			

def UpdateTrainers():
	allPkmnData = pokemonservice.GetAllPokemon()
	updateList: list[Trainer] = []
	for t in GetManyDocs('Trainer', {}, {'_id':0}):
		try:
			newTrainer = Trainer.from_dict({
				'UserId': t['UserId'] if 'UserId' in t else 0,
				'ServerId': t['ServerId'] if 'ServerId' in t else 0,
				'Money': t['Money'] if 'Money' in t else 0,
				'Items': {
					'1': (t['Pokeballs']['4'] if '4' in t['Pokeballs'] else 0) if 'Pokeballs' in t else 0,
					'2': (t['Pokeballs']['3'] if '3' in t['Pokeballs'] else 0) if 'Pokeballs' in t else 0,
					'3': (t['Pokeballs']['2'] if '2' in t['Pokeballs'] else 0) if 'Pokeballs' in t else 0,
					'4': (t['Pokeballs']['1'] if '1' in t['Pokeballs'] else 0) if 'Pokeballs' in t else 0,
					'17': (t['Potions']['1'] if '1' in t['Potions'] else 0) if 'Potions' in t else 0,
					'26': (t['Potions']['2'] if '2' in t['Potions'] else 0) if 'Potions' in t else 0,
					'25': (t['Potions']['3'] if '3' in t['Potions'] else 0) if 'Potions' in t else 0,
					'24': (t['Potions']['4'] if '4' in t['Potions'] else 0) if 'Potions' in t else 0,
					'50': (t['Candies']['1'] if '1' in t['Candies'] else 0) if 'Candies' in t else 0,
					'80': (t['EvolutionItems']['80'] if '80' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'81': (t['EvolutionItems']['81'] if '81' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'82': (t['EvolutionItems']['82'] if '82' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'83': (t['EvolutionItems']['83'] if '83' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'84': (t['EvolutionItems']['84'] if '84' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'85': (t['EvolutionItems']['85'] if '85' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'107': (t['EvolutionItems']['107'] if '107' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'108': (t['EvolutionItems']['108'] if '108' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'109': (t['EvolutionItems']['109'] if '109' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'110': (t['EvolutionItems']['110'] if '110' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'198': (t['EvolutionItems']['198'] if '198' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'203': (t['EvolutionItems']['203'] if '203' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'204': (t['EvolutionItems']['204'] if '204' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'210': (t['EvolutionItems']['210'] if '210' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'212': (t['EvolutionItems']['212'] if '212' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'229': (t['EvolutionItems']['229'] if '229' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'298': (t['EvolutionItems']['298'] if '298' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'299': (t['EvolutionItems']['299'] if '299' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'300': (t['EvolutionItems']['300'] if '300' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'301': (t['EvolutionItems']['301'] if '301' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'302': (t['EvolutionItems']['302'] if '302' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'303': (t['EvolutionItems']['303'] if '303' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'304': (t['EvolutionItems']['304'] if '304' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'686': (t['EvolutionItems']['686'] if '686' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'687': (t['EvolutionItems']['687'] if '687' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'885': (t['EvolutionItems']['885'] if '885' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1167': (t['EvolutionItems']['1167'] if '1167' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1174': (t['EvolutionItems']['1174'] if '1174' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1175': (t['EvolutionItems']['1175'] if '1175' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1183': (t['Candies']['2'] if '2' in t['Candies'] else 0) if 'Candies' in t else 0,
					'1185': (t['Candies']['3'] if '3' in t['Candies'] else 0) if 'Candies' in t else 0,
					'1311': (t['EvolutionItems']['1311'] if '1311' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1312': (t['EvolutionItems']['1312'] if '1312' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1633': (t['EvolutionItems']['1633'] if '1633' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1643': (t['EvolutionItems']['1643'] if '1643' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'1677': (t['EvolutionItems']['1677'] if '1677' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'2045': (t['EvolutionItems']['2045'] if '2045' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'10001': (t['EvolutionItems']['10001'] if '10001' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0,
					'10002': (t['EvolutionItems']['10002'] if '10002' in t['EvolutionItems'] else 0) if 'EvolutionItems' in t else 0
				},
				'OwnedPokemon': t['OwnedPokemon'] if 'OwnedPokemon' in t else [],
				'Pokedex': t['Pokedex'] if 'Pokedex' in t else [],
				'Shinydex': t['Shinydex'] if 'Shinydex' in t else [],
				'Formdex': t['Formdex'] if 'Formdex' in t else [],
				'Team': t['Team'] if 'Team' in t else [],
				'Badges': t['Badges'] if 'Badges' in t else [],
				'SpTrainerWins': t['SpTrainerWins'] if 'SpTrainerWins' in t else [],
				'GymAttempts': t['GymAttempts'] if 'GymAttempts' in t else [],
				'Eggs': t['Eggs'] if 'Eggs' in t else [],
				'Daycare': t['Daycare'] if 'Daycare' in t else {},
				'LastDaily': t['LastDaily'] if 'LastDaily' in t else None,
				'Region': 1,
				'DailyMission': t['DailyMission'] if 'DailyMission' in t else None,
				'WeeklyMission': t['WeeklyMission'] if 'WeeklyMission' in t else None
			})
			
			for p in newTrainer.OwnedPokemon:
				if p.Pokemon_Id == 10057:
					newTrainer.OwnedPokemon.remove(p)
				else:
					pData = next(pd for pd in allPkmnData if p.Pokemon_Id == pd.Id)
					p.Nature = choice(statservice.GetAllNatures()).Id
					p.IVs = {
						"1": choice(range(32)),
						"2": choice(range(32)),
						"3": choice(range(32)),
						"4": choice(range(32)),
						"5": choice(range(32)),
						"6": choice(range(32)),
					}
					p.CurrentAilment = None
					p.CurrentHP = statservice.GenerateStat(p, pData, StatEnum.HP)
					p.LearnedMoves = []
					moveservice.GenerateMoves(p, pData)
				if p.Pokemon_Id == 132 and p.Id in newTrainer.Team:
					newTrainer.Team = [t for t in newTrainer.Team if t != p.Id]

			badges: list[int] = []
			for b in newTrainer.Badges:
				if 34 <= b < 41:
					badges.append(b+1)
				elif 42 <= b < 49:
					badges.append(b+2)
				elif b < 1000:
					badges.append(b+11)
				else:
					badges.append(b)
				

			if newTrainer.ServerId and newTrainer.UserId:
				updateList.append(newTrainer)
		except Exception:
			print(f'Trainer failed to update: {t["UserId"]}-{t["ServerId"]}')
			pass
	print(len(updateList))
	return updateList
		
if len(sys.argv) == 2 and sys.argv[1] == 'prodbuild':
  load_dotenv('.env')
else:
  load_dotenv('.env.local')

try:
	print('Cache Delete')
	os.remove('dataaccess/utility/cache.sqlite3')
except Exception as e:
	pass
print('Trainers:')
i = 0
for trainer in UpdateTrainers():
	print(f'{i} Trainer: {trainer.ServerId}-{trainer.UserId}')
	trainerda.UpsertSingleTrainer(trainer)
	i += 1
i = 0
print('Servers:')
for server in UpdateServers():
	print(f'{i} Server: {server.ServerId}-{server.ServerName}')
	serverda.UpsertSingleServer(server)
	i += 1