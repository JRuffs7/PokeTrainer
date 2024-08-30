from dataaccess.utility import sqliteda
from models.Trainer import Trainer

collection: str = 'Trainer'

def CheckTrainer(serverId: int, userId: int):
  return sqliteda.KeyExists(collection, f'{serverId}{userId}')

def GetSingleTrainer(serverId: int, userId: int) -> Trainer|None:
  return sqliteda.Load(collection, f'{serverId}{userId}')

def UpsertSingleTrainer(trainer: Trainer):
  sqliteda.Save(collection, f'{trainer.ServerId}{trainer.UserId}', trainer)

def DeleteSingleTrainer(trainer: Trainer):
  sqliteda.Remove(collection, f'{trainer.ServerId}{trainer.UserId}')

def GetTrainers(serverId: int) -> list[Trainer]:
  return [t for t in sqliteda.LoadAll(collection) if t['ServerId'] == serverId]
