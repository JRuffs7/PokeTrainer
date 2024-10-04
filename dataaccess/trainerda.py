from dataaccess.utility import sqliteda
from globals import to_dict
from models.Trainer import Trainer

collection: str = 'Trainer'

def CheckTrainer(serverId: int, userId: int):
  return sqliteda.KeyExists(collection, f'{serverId}{userId}')

def GetSingleTrainer(serverId: int, userId: int):
  trainer = sqliteda.Load(collection, f'{serverId}{userId}')
  return Trainer.from_dict(to_dict(trainer)) if trainer else None

def UpsertSingleTrainer(trainer: Trainer):
  sqliteda.Save(collection, f'{trainer.ServerId}{trainer.UserId}', trainer)

def DeleteSingleTrainer(trainer: Trainer):
  sqliteda.Remove(collection, f'{trainer.ServerId}{trainer.UserId}')

def GetTrainers(serverId: int):
  return [Trainer.from_dict(to_dict(t)) for t in sqliteda.LoadAll(collection) if t['ServerId'] == serverId]
