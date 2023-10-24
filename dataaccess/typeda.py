from flask import json

from models.Type import Type

typeFile = "collections/types.json"


def GetTypeByName(type):
  return next((Type(t) for t in GetJson() if t['Type'].lower() == type.lower()), None)


def GetJson():
  with open(typeFile, encoding="utf-8") as f:
    return json.load(f)
