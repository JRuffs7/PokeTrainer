from dataaccess.utility.jsonreader import GetJson

from models.Zone import Zone

zoneFile = "collections/zones.json"

def GetAllZones():
  zones = GetJson(zoneFile)
  return [Zone(z) for z in zones]