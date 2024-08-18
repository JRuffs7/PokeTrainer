from threading import Thread

from dataaccess.utility import mongodb, sqliteda
from globals import to_dict
from models.Trainer import Trainer

collection: str = 'Trainer'

def CheckTrainer(serverId: int, userId: int):
  if sqliteda.KeyExists(collection, f'{serverId}{userId}'):
    return True
  trainer = mongodb.GetSingleDoc(collection, {
        'ServerId': serverId,
        'UserId': userId
  })
  return (trainer is not None)

def GetTrainer(serverId: int, userId: int) -> Trainer|None:
  key = f'{serverId}{userId}'
  trainer = sqliteda.Load(collection, key)
  if not trainer:
    train = mongodb.GetSingleDoc(collection, {
        'ServerId': serverId,
        'UserId': userId
    })
    trainer = Trainer.from_dict(train) if train else None
    if trainer:
      sqliteda.Save(collection, key, trainer)
  return trainer

def GetAllTrainers():
  return mongodb.GetManyDocs(collection, {}, {'_id':0}) or []

def GetWishlistTrainers(serverId: int, pokemonId: int) -> list[int]:
  train = mongodb.GetManyDocs(
    collection, 
    { 'ServerId': serverId, 'Wishlist': pokemonId },
    { 'UserId': 1, '_id': 0 })
  trainer = [int(t['UserId']) for t in train] if train else []
  return trainer

def UpsertTrainer(trainer: Trainer):
  sqliteda.Save(collection, f'{trainer.ServerId}{trainer.UserId}', trainer)
  thread = Thread(target=PushTrainerToMongo, args=(trainer, ))
  thread.start()
  return trainer


def DeleteTrainer(trainer: Trainer):
  sqliteda.Remove(collection, f'{trainer.ServerId}{trainer.UserId}')
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

def PushTrainers(trainers: list[Trainer]):
  updateList = []
  for trainer in trainers:
    sqliteda.Save('Trainer', f'{trainer.ServerId}{trainer.UserId}', trainer)
    updateList.append({
      'filter': {
        'ServerId': trainer.ServerId,
        'UserId': trainer.UserId
      }, 
      'object': to_dict(trainer)
    })
  mongodb.UpsertManyDocs(collection, updateList)


def DeleteTrainerFromMongo(serverId, userId):
  mongodb.DeleteDocs(collection, {
      'ServerId': serverId,
      'UserId': userId
  })
  return
