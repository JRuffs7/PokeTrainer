import logging
import os

from pymongo.mongo_client import MongoClient

errorLog = logging.getLogger('error')

def GetSingleDoc(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      return coll.find_one(filters, {'_id': False})
  except Exception as e:
    errorLog.error(f"Mongo Exception: {e}")
    return None


def GetManyDocs(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      return list(coll.find(filters, {'_id': False}))
  except Exception as e:
    errorLog.error(f"Mongo Exception: {e}")
    return None


def UpsertSingleDoc(collection, filters, object):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      coll.replace_one(filters, object, upsert=True)
  except Exception as e:
    errorLog.error(f"Mongo Exception: {e}")
    return None


def DeleteDocs(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      coll.delete_one(filters)
  except Exception as e:
    errorLog.error(f"Mongo Exception: {e}")
    return None
