from dataaccess.utility.jsonreader import GetJson

from models.Type import Type

typeFile = "collections/types.json"


def GetAllTypes():
  return [Type(t) for t in GetJson(typeFile)]