from dataaccess import statda

def AttackEffect(attackType: int, defendingTypes: list[int]):
  types = statda.GetAllTypes()
  dTypeOne = next(t for t in types if t.Id == defendingTypes[0])
  dTypeTwo = next(t for t in types if t.Id == defendingTypes[0]) if len(defendingTypes) > 1 else None
  defendOne = 0 if attackType in dTypeOne.Immune else 2 if attackType in dTypeOne.Weakness else 0.5 if attackType in dTypeOne.Resistant else 1
  defendTwo = (0 if attackType in dTypeTwo.Immune else 2 if attackType in dTypeTwo.Weakness else 0.5 if attackType in dTypeTwo.Resistant else 1) if dTypeTwo else 1
  return defendOne * defendTwo


def TypeWeakness(attacking, defending):
  defenseType = next(t for t in statda.GetAllTypes() if t.Name.lower() == defending.lower())

  if attacking in defenseType.Weakness:
      return 1
  if attacking in defenseType.Resistant:
      return -1
  if attacking in defenseType.Immune:
      return -2
  return 0

def TypeMatch(attackTypes: list[int], defendTypes: list[int]):
  if len(attackTypes) == 1:
    fightOne = TypeWeakness(attackTypes[0].lower(), defendTypes[0].lower())
    fightTwo = TypeWeakness(attackTypes[0].lower(), defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
    if fightOne == -2 or fightTwo == -2:
      return -5
    return fightOne + fightTwo
  else:
    fightA1 = TypeWeakness(attackTypes[0].lower(), defendTypes[0].lower())
    fightA2 = TypeWeakness(attackTypes[0].lower(), defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
    firstType = -5 if fightA1 == -2 or fightA2 == -2 else fightA1 + fightA2 

    fightB1 = TypeWeakness(attackTypes[1].lower(), defendTypes[0].lower())
    fightB2 = TypeWeakness(attackTypes[1].lower(), defendTypes[1].lower() if len(defendTypes) > 1 else defendTypes[0].lower())
    secondType = -5 if fightB1 == -2 or fightB2 == -2 else fightB1 + fightB2 

    #One type is immune
    if firstType == -5 or secondType == -5:
      return firstType if secondType == -5 else secondType
    
    #One type is Super Effective
    if firstType == 2 or secondType == 2:
      return 4 if firstType == 2 and secondType == 2 else 2
    
    return firstType + secondType