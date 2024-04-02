from dataaccess.utility.jsonreader import GetJson

from models.Help import Help

botHelp = "files/helpfiles/bothelp.json"
commandHelp = "files/helpfiles/commandhelp.json"


def GetAllHelpCommands(isAdmin: bool):
  jsonFile = GetJson(commandHelp)
  serverComs = [Help(x) for x in jsonFile['Server']]
  serverComs = list(filter((lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin), serverComs))
  serverComs.sort(key=lambda x: x.Name)
  trainerComs = [Help(x) for x in jsonFile['Trainer']]
  trainerComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, trainerComs))
  trainerComs.sort(key=lambda x: x.Name)
  gymComs = [Help(x) for x in jsonFile['Gym']]
  gymComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, gymComs))
  gymComs.sort(key=lambda x: x.Name)
  tradeComs = [Help(x) for x in jsonFile['Trade']]
  tradeComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, tradeComs))
  tradeComs.sort(key=lambda x: x.Name)
  shopComs = [Help(x) for x in jsonFile['Shop']]
  shopComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, shopComs))
  shopComs.sort(key=lambda x: x.Name)
  pokemonComs = [Help(x) for x in jsonFile['Pokemon']]
  pokemonComs = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, pokemonComs))
  pokemonComs.sort(key=lambda x: x.Name)
  actions = [Help(x) for x in jsonFile['Actions']]
  actions = list(filter(lambda x: (x.RequiresAdmin and isAdmin) or not x.RequiresAdmin, actions))
  actions.sort(key=lambda x: x.Name)
  commands = { 'Server': serverComs, 'Trainer': trainerComs, 'Gym': gymComs, 'Trade': tradeComs, 'Shop': shopComs, 'Pokemon': pokemonComs, 'Actions': actions }
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


def BuildFullHelp(isAdmin: bool):
  fullHelp = GetJson(botHelp)
  commands = GetAllHelpCommands(isAdmin)
  summaries = [str(x) for x in fullHelp]
  commandSummary = '__**COMMANDS**__\n\nThis is a list of commands and a simplified description. For further details on each command, try using the **/help** sub commands.'
  newline = "\n"
  for h in commands:
    if h != 'Actions' and commands[h]:
      commandSummary += f"{newline}{newline}__{h} Commands__"
      helpList = commands[h]
      for helpObj in helpList:
        commandSummary += f"\n**/{helpObj.Name}** - {helpObj.ShortString}"
  summaries.append(commandSummary)
  return summaries

