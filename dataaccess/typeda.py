from flask import json

from models.Type import Type

typeFile = "collections/types.json"


def GetAllTypes():
  return [Type(t) for t in GetJson()]


def GetJson():
  with open(typeFile, encoding="utf-8") as f:
    return json.load(f)
