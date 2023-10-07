from threading import Thread

from dataaccess.utility import mongodb
from globals import to_dict
from models.Trainer import Trainer

collection: str = 'Trainer'
trainerCache = {}


def GetTrainer(userId, serverId):
  if f"{userId}{serverId}" in trainerCache:
    return trainerCache[f"{userId}{serverId}"]
  train = mongodb.GetSingleDoc(collection, {
      'UserId': userId,
      'ServerId': serverId
  })
  tr = Trainer(train) if train else None
  if tr:
    trainerCache[f"{userId}{serverId}"] = tr
  return tr


def UpsertTrainer(trainer: Trainer):
  trainerCache[f"{trainer.UserId}{trainer.ServerId}"] = trainer
  thread = Thread(target=PushTrainerToMongo, args=(trainer, ))
  thread.start()
  return trainer


def DeleteTrainer(trainer: Trainer):
  del trainerCache[f"{trainer.UserId}{trainer.ServerId}"]
  thread = Thread(target=DeleteTrainerFromMongo,
                  args=(trainer.UserId, trainer.ServerId))
  thread.start()
  return trainer


def PushTrainerToMongo(trainer: Trainer):
  mongodb.UpsertSingleDoc(collection, {
      'UserId': trainer.UserId,
      'ServerId': trainer.ServerId,
  }, to_dict(trainer))
  return


def DeleteTrainerFromMongo(userId, serverId):
  mongodb.DeleteDocs(collection, {
      'UserId': userId,
      'ServerId': serverId,
  })
  return
