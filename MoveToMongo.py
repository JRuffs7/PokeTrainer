import os
from dotenv import load_dotenv
from dataaccess import serverda, trainerda
from dataaccess.utility import sqliteda
from globals import to_dict
from models.Server import Server
from models.Trainer import Trainer

def LoadTrainers(trainers: list[Trainer]):
	for trainer in trainers:
		print(f'Trainer: {trainer.ServerId} - {trainer.UserId}')
		if not trainerda.UpsertSingleTrainer(trainer):
			print(f'Error')

def LoadServers(servers: list[Server]):
	for server in servers:
		print(f'Server: {server.ServerId}')
		if not serverda.UpsertSingleServer(server):
			print(f'Error')

load_dotenv('.env')
allTrainers = [Trainer.from_dict(to_dict(t)) for t in sqliteda.LoadAll('Trainer')]
allServers = [Server.from_dict(to_dict(t)) for t in sqliteda.LoadAll('Server')]
LoadTrainers(allTrainers)
LoadServers(allServers)