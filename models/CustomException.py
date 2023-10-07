class TrainerInvalidException(Exception):
  "Raised when a user attempts to run a command without an existing trainer"
  pass


class ServerInvalidException(Exception):
  "Raised when a user attempts to run a command in an unregistered server"
  pass
