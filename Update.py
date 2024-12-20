from dotenv import load_dotenv
from models.Move import MoveData
from models.Trainer import Trainer
from services import moveservice, trainerservice


def UpdateMaxPP(trainer: Trainer, moves: list[MoveData]):
	for p in trainer.OwnedPokemon:
		print(f'{p.Pokemon_Id}')
		for m in p.LearnedMoves:
			m.MaxPP = next(mo for mo in moves if mo.Id == m.MoveId).BasePP
	

load_dotenv('.env')
allMoves = moveservice.GetAllMoves()
for tr in trainerservice.GetAllTrainers():
	print(f'----------- {tr.UserId} -----------')
	UpdateMaxPP(tr, allMoves)
	trainerservice.UpsertTrainer(tr)