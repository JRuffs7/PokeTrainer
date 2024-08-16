from dataaccess.utility.jsonreader import GetJson

from models.Move import Move

moveFile = "collections/moves.json"


def GetAllMoves():
  moves = GetJson(moveFile)
  return [Move(x) for x in moves]


def GetMovesByType(type):
  moves = GetJson(moveFile)
  return [Move(x) for x in moves if type in x['Types']]


def GetMovesByProperty(searchVals: list, property: str):
  moves = GetJson(moveFile)
  return [Move(x) for x in moves if searchVals.__contains__(x[property])]


def GetUniqueMovesProperty(prop):
  moves = GetJson(moveFile)
  return set([x[prop] for x in moves])