from dataaccess.utility.jsonreader import GetJson

from models.Zone import Zone

zoneFile = "collections/zones.json"

def GetAllZones():
  return [Zone(z) for z in GetJson(zoneFile)]