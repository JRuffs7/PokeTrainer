import json

from models.Help import Help

botHelp = "files/helpfiles/bothelp.json"
commandHelp = "files/helpfiles/commandhelp.json"


def GetAllHelpCommands(isAdmin: bool):
  serverComs = [Help(x) for x in GetJson(commandHelp)['Server']]
  serverComs = list(filter((lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin), serverComs))
  serverComs.sort(key=lambda x: x.Name)
  trainerComs = [Help(x) for x in GetJson(commandHelp)['Trainer']]
  trainerComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, trainerComs))
  trainerComs.sort(key=lambda x: x.Name)
  pokemonComs = [Help(x) for x in GetJson(commandHelp)['Pokemon']]
  pokemonComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, pokemonComs))
  pokemonComs.sort(key=lambda x: x.Name)
  gymComs = [Help(x) for x in GetJson(commandHelp)['Gym']]
  gymComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, gymComs))
  gymComs.sort(key=lambda x: x.Name)
  shopComs = [Help(x) for x in GetJson(commandHelp)['Shop']]
  shopComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, shopComs))
  shopComs.sort(key=lambda x: x.Name)
  actions = [Help(x) for x in GetJson(commandHelp)['Actions']]
  actions = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, actions))
  actions.sort(key=lambda x: x.Name)
  commands = { 'Server': serverComs, 'Trainer': trainerComs, 'Pokemon': pokemonComs, 'Gym': gymComs, 'Shop': shopComs, 'Actions': actions }
  return commands


def BuildCommandHelp(command: str, isAdmin: bool):
  fullHelp = GetAllHelpCommands(isAdmin)
  for hlp in fullHelp:
    helpCom = next((h for h in fullHelp[hlp] if h.Name.lower() == command.lower()), None)
    if helpCom:
      if not helpCom.RequiresAdmin or (helpCom.RequiresAdmin and isAdmin):
        return helpCom
      else:
        break
  return None


def BuildFullHelp():
  fullHelp = GetJson(botHelp)
  commands = GetAllHelpCommands(True)
  summaries = [str(x) for x in fullHelp]
  commandSummary = '__**COMMANDS**__\n\nThis is a list of commands and a simplified description. For further details on each command, try using the **/help** sub commands.'
  newline = "\n"
  for h in commands:
    if h != 'Actions':
      commandSummary += f"{newline}{newline}__{h} Commands__"
      helpList = commands[h]
      for helpObj in helpList:
        commandSummary += f"\n**/{helpObj.Name}** - {helpObj.ShortString}"
  summaries.append(commandSummary)
  return summaries


def GetJson(file: str):
  with open(file, encoding="utf8") as f:
    return json.load(f)
