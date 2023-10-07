import json

botHelp = "files/helpfiles/bothelp.json"
commandHelp = "files/helpfiles/commandhelp.json"


def BuildCommandHelp(command: str, isAdmin: bool):
  helpObj = GetJson(commandHelp)

  if not helpObj or command.lower() not in helpObj:
    return (False, "")

  commandHelpObj = helpObj[command.lower()]
  if commandHelpObj["requireadmin"] and not isAdmin:
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
