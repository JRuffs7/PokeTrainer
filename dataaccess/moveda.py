from dataaccess.utility.jsonreader import GetJson

from models.Move import MoveData

moveFile = "collections/moves.json"


def GetAllMoves():
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves]


def GetMovesByType(type: int):
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves if type == x['MoveType']]


def GetMovesByProperty(searchVals: list, property: str):
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves if searchVals.__contains__(x[property])]


def GetUniqueMovesProperty(prop):
  moves = GetJson(moveFile)
  return set([x[prop] for x in moves])

def GetMovesByIdAndMachine(idList: list[int], machineList: list[str]):
  moves = GetJson(moveFile)
  return set([MoveData(x) for x in moves if x['Id'] in idList or x['MachineID'] in machineList])