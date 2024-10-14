from dataaccess.utility.jsonreader import GetJson

from models.Move import MoveData

moveFile = "collections/moves.json"


def GetAllMoves():
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves]

def GetTMMoves():
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves if x['Cost']]


def GetMovesByType(type: int):
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves if type == x['MoveType']]


def GetMovesByProperty(searchVals: list, property: str):
  moves = GetJson(moveFile)
  return [MoveData(x) for x in moves if searchVals.__contains__(x[property])]
