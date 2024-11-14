import logging
import os
from pymongo.mongo_client import MongoClient

errorLog = logging.getLogger('error')
debugLog = logging.getLogger('debug')

def NumberOfDocs(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGOCONN')) as client:
      coll = client[os.environ.get('MONGONAME')][collection]
      return coll.count_documents(filters)
  except Exception as e:
    errorLog.error(f'Mongo Number of Docs Exception: {e}')
    return 0

def GetSingleDoc(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGOCONN')) as client:
      coll = client[os.environ.get('MONGONAME')][collection]
      return coll.find_one(filters, {'_id': False})
  except Exception as e:
    errorLog.error(f'Mongo Get Single Exception: {e}')
    return None
  
def GetManyDocs(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGOCONN')) as client:
      coll = client[os.environ.get('MONGONAME')][collection]
      return list(coll.find(filters, {'_id': False}))
  except Exception as e:
    errorLog.error(f'Mongo Get Many Exception: {e}')
    return None
  
def UpsertSingleDoc(collection, filters, object):
  try:
    with MongoClient(os.environ.get('MONGOCONN')) as client:
      coll = client[os.environ.get('MONGONAME')][collection]
      coll.replace_one(filters, object, upsert=True)
      debugLog.info(f'UPDATE')
  except Exception as e:
    errorLog.error(f'Mongo Upsert Exception: {e}')
    return None
  
def DeleteDocs(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGOCONN')) as client:
      coll = client[os.environ.get('MONGONAME')][collection]
      coll.delete_one(filters)
  except Exception as e:
    errorLog.error(f'Mongo Delete Exception: {e}')
    return None