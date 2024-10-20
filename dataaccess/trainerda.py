from dataaccess.utility import mongodb
from globals import to_dict
from models.Trainer import Trainer

collection: str = 'Trainer'

def CheckTrainer(serverId: int, userId: int):
  return mongodb.NumberOfDocs(collection, {
        'ServerId': serverId,
        'UserId': userId
    }) == 1

def GetSingleTrainer(serverId: int, userId: int):
  trainer = mongodb.GetSingleDoc(collection, {
        'ServerId': serverId,
        'UserId': userId
    })
  return Trainer.from_dict(trainer) if trainer else None

def UpsertSingleTrainer(trainer: Trainer):
  mongodb.UpsertSingleDoc(collection, {
      'ServerId': trainer.ServerId,
      'UserId': trainer.UserId
  }, to_dict(trainer))
  return True

def DeleteSingleTrainer(trainer: Trainer):
  mongodb.DeleteDocs(collection, {
      'ServerId': trainer.ServerId,
      'UserId': trainer.UserId
  })
  return True