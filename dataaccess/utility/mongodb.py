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
    if 'temporary' in str(e).lower():
      errorLog.error(f"Mongo Get Single Exception: Temporary failure in name resolution.\nCollection: {collection}\nfilters: {filters}")
    if 'not known' in str(e).lower():
      errorLog.error(f"Mongo Get Single Exception: Name or service not known.\nCollection: {collection}\nfilters: {filters}")
    return None


def GetManyDocs(collection, filters, fields):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      return list(coll.find(filters, fields))
  except Exception as e:
    if 'temporary' in str(e).lower():
      errorLog.error(f"Mongo Get Many Exception: Temporary failure in name resolution.\nCollection: {collection}\nfilters: {filters}")
    if 'not known' in str(e).lower():
      errorLog.error(f"Mongo Get Many Exception: Name or service not known.\nCollection: {collection}\nfilters: {filters}")
    return None


def UpsertSingleDoc(collection, filters, object):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      coll.replace_one(filters, object, upsert=True)
  except Exception as e:
    if 'temporary' in str(e).lower():
      errorLog.error(f"Mongo Upsert Exception: Temporary failure in name resolution.\nCollection: {collection}\nfilters: {filters}")
    if 'not known' in str(e).lower():
      errorLog.error(f"Mongo Upsert Exception: Name or service not known.\nCollection: {collection}\nfilters: {filters}")
    return None


def DeleteDocs(collection, filters):
  try:
    with MongoClient(os.environ.get('MONGO_CONN_STRING')) as cluster:
      coll = cluster[os.environ.get('MONGO_DB_NAME')][collection]
      coll.delete_one(filters)
  except Exception as e:
    if 'temporary' in str(e).lower():
      errorLog.error(f"Mongo Delete Exception: Temporary failure in name resolution.\nCollection: {collection}\nfilters: {filters}")
    if 'not known' in str(e).lower():
      errorLog.error(f"Mongo Delete Exception: Name or service not known.\nCollection: {collection}\nfilters: {filters}")
    return None
