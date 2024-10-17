

from dataaccess import commandlockda

def IsLocked(serverId: int, userId: int):
  return commandlockda.CheckLock(serverId, userId)

def AddLock(serverId: int, userId: int):
  return commandlockda.AddLock(serverId, userId)

def DeleteLock(serverId: int, userId: int):
  return commandlockda.DeleteLock(serverId, userId)

def DeleteAllLocks():
  return commandlockda.DeleteAllLocks()


def IsEliteFourLocked(serverId: int, userId: int):
  return commandlockda.CheckEliteFourLock(serverId, userId)

def AddEliteFourLock(serverId: int, userId: int):
  return commandlockda.AddEliteFourLock(serverId, userId)

def DeleteEliteFourLock(serverId: int, userId: int):
  return commandlockda.DeleteEliteFourLock(serverId, userId)