from dataaccess import typeda

def TypeWeakness(attacking, defending):
    defenseType = typeda.GetTypeByName(defending)

    if attacking in defenseType.Weakness:
        return 1
    if attacking in defenseType.Resistant:
        return -1
    if attacking in defenseType.Immune:
        return -2
    return 0