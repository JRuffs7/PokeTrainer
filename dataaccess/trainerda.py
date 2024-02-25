from threading import Thread

from dataaccess.utility import mongodb
from globals import to_dict
from models.Trainer import Trainer

collection: str = 'Trainer'
trainerCache = {}


def GetTrainer(serverId, userId):
  key = f"{serverId}{userId}"
  if key in trainerCache:
    return trainerCache[key]
  train = mongodb.GetSingleDoc(collection, {
      'ServerId': serverId,
      'UserId': userId
  })
  tr = Trainer(train) if train else None
  if tr:
    trainerCache[key] = tr
  return tr


def UpsertTrainer(trainer: Trainer):
  trainerCache[f"{trainer.ServerId}{trainer.UserId}"] = trainer
  thread = Thread(target=PushTrainerToMongo, args=(trainer, ))
  thread.start()
  return trainer


def DeleteTrainer(trainer: Trainer):
  del trainerCache[f"{trainer.ServerId}{trainer.UserId}"]
  thread = Thread(target=DeleteTrainerFromMongo,
                  args=(trainer.ServerId, trainer.UserId))
  thread.start()
  return trainer


def PushTrainerToMongo(trainer: Trainer):
  mongodb.UpsertSingleDoc(collection, {
      'ServerId': trainer.ServerId,
      'UserId': trainer.UserId
  }, to_dict(trainer))
  return


def DeleteTrainerFromMongo(serverId, userId):
  mongodb.DeleteDocs(collection, {
      'ServerId': serverId,
      'UserId': userId
  })
  return
