from dataaccess import zoneda


def GetAllZones():
  return zoneda.GetAllZones()

def GetZone(id: int):
  return next(z for z in zoneda.GetAllZones() if z.Id == id)