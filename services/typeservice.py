from dataaccess import typeda
from models.Type import Type

def TypeWeakness(attacking, defending):
    defenseType = next(t for t in GetAllTypes() if t.Name.lower() == defending.lower())

    if attacking in defenseType.Weakness:
        return 1
    if attacking in defenseType.Resistant:
        return -1
    if attacking in defenseType.Immune:
        return -2
    return 0

def GetAllTypes():
    return typeda.GetAllTypes()