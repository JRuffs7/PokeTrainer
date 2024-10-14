from dataaccess.utility.jsonreader import GetJson

from models.Stat import Ailment
from models.Stat import Stat
from models.Stat import Nature
from models.Stat import Type

statFile = "collections/stats.json"
natureFile = "collections/natures.json"
typeFile = "collections/types.json"
ailmentFile = "collections/ailments.json"


def GetAllStats():
  stats = GetJson(statFile)
  return [Stat(s) for s in stats]

def GetAllNatures():
  natures = GetJson(natureFile)
  return [Nature(n) for n in natures]

def GetAllTypes():
  types = GetJson(typeFile)
  return [Type(t) for t in types]

def GetAllAilments():
  ailments = GetJson(ailmentFile)
  return [Ailment(a) for a in ailments]