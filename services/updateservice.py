import logging
from random import choice
from dataaccess import trainerda
from models.Trainer import Trainer
from services import pokemonservice, statservice

errorLogger = logging.getLogger('error')

def UpdateTrainers():
	allPkmnData = pokemonservice.GetAllPokemon()
	updateList: list[Trainer] = []
	for t in trainerda.GetAllTrainers() or []:
		try:
			print(t['UserId'])
			newTrainer = Trainer.from_dict({
				'UserId': t['UserId'] if 'UserId' in t else 0,
				'ServerId': t['ServerId'] if 'ServerId' in t else 0,
				'Health': t['Health'] if 'Health' in t else 0,
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
				'Wishlist': t['Wishlist'] if 'Wishlist' in t else [],
				'LastSpawnTime': t['LastSpawnTime'] if 'LastSpawnTime' in t else None,
				'LastDaily': t['LastDaily'] if 'LastDaily' in t else None,
				'Shop': t['Shop'] if 'Shop' in t else None,
				'CurrentZone': t['CurrentZone'] if 'CurrentZone' in t else 0,
				'DailyMission': t['DailyMission'] if 'DailyMission' in t else None,
				'WeeklyMission': t['WeeklyMission'] if 'WeeklyMission' in t else None
			})
			for p in newTrainer.OwnedPokemon:
				if p.Pokemon_Id == 10057:
					newTrainer.OwnedPokemon.remove(p)
				else:
					print(p.Pokemon_Id)
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
					p.CurrentHP = statservice.GenerateHP(p.IVs["1"], pData.BaseStats["1"], p.Level)
					p.LearnedMoves = []
					slot = 0
					for move in dict(reversed(sorted(pData.LevelUpMoves.items(), key=lambda move: move[1]))):
						if pData.LevelUpMoves[move] <= p.Level:
							p.LearnedMoves.append(int(move))
							slot += 1
						if slot == 4:
							break
			updateList.append(newTrainer)
		except Exception as e:
			errorLogger.error(f"Could not update trainer: {t['UserId']}-{t['ServerId']}\n{e}")
			pass
	trainerda.PushTrainers(updateList)
		
	