import json

botHelp = "files/helpfiles/bothelp.json"
commandHelp = "files/helpfiles/commandhelp.json"


def GetAllHelpCommands():
  serverComs = [x['name'] for x in GetJson(commandHelp)['Server']]
  trainerComs = [x['name'] for x in GetJson(commandHelp)['Trainer']]
  pokemonComs = [x['name'] for x in GetJson(commandHelp)['Pokemon']]
  shopComs = [x['name'] for x in GetJson(commandHelp)['Shop']]
  actions = [x['name'] for x in GetJson(commandHelp)['Actions']]
  commands = serverComs + trainerComs + pokemonComs + shopComs + actions
  commands.sort()
  return commands


def BuildCommandHelp(command: str, interaction):
  helpObj = GetJson(commandHelp)

  if not helpObj or command.lower() not in helpObj:
    return (False, "")

  commandHelpObj = helpObj[command.lower()]
  if commandHelpObj["requireadmin"] and not interaction.user.guild_permissions.administrator:
    return (False, "")

  return (True, commandHelpObj["helpstring"])


def BuildFullHelp():
  helpObj = GetJson(botHelp)

  gl = helpObj["General"]
  gm = helpObj["Gameplay"]
  cm = helpObj["Commands"]

  return [gl, gm, cm]


def GetJson(file: str):
  with open(file) as f:
    return json.load(f)
