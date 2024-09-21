

from dataaccess import commandlockda

def IsLocked(serverId: int, userId: int):
  return commandlockda.CheckLock(serverId, userId)


def AddLock(serverId: int, userId: int):
  return commandlockda.AddLock(serverId, userId)


def DeleteLock(serverId: int, userId: int):
  return commandlockda.DeleteLock(serverId, userId)