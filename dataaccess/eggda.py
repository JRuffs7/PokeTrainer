from dataaccess.utility.jsonreader import GetJson

from models.Egg import Egg

eggFile = "collections/eggs.json"

def GetAllEggs():
  eggs = GetJson(eggFile)
  return [Egg(e) for e in eggs]