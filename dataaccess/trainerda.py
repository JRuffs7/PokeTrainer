from threading import Thread

from dataaccess.utility import mongodb, sqliteda
from globals import to_dict
from models.Trainer import Trainer

collection: str = 'Trainer'

def GetTrainer(serverId, userId) -> Trainer|None:
  key = f"{serverId}{userId}"
  trainer = sqliteda.Load(key)
  if not trainer:
    train = mongodb.GetSingleDoc(collection, {
        'ServerId': serverId,
        'UserId': userId
    })
    trainer = Trainer(train) if train else None
    if trainer:
      sqliteda.Save(key, trainer)
  return trainer


def UpsertTrainer(trainer: Trainer):
  sqliteda.Save(f"{trainer.ServerId}{trainer.UserId}", trainer)
  thread = Thread(target=PushTrainerToMongo, args=(trainer, ))
  thread.start()
  return trainer


def DeleteTrainer(trainer: Trainer):
  sqliteda.Remove(f"{trainer.ServerId}{trainer.UserId}")
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
