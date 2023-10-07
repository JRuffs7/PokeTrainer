import base64
import hashlib
import os


def HashPassword(password):
  t_sha = hashlib.sha512()
  t_sha.update(bytes(password, 'utf-8'))
  return base64.urlsafe_b64encode(t_sha.digest()).decode('utf-8')


def GetToken(header):
  if header is None:
    return "Invalid"
  return base64.b64decode(
      header.__str__().split(' ')[1]).decode('utf-8').split(":")


def ValidateToken(token):
  tokenObj = GetToken(token)
  if tokenObj[0] != "PokeTrainer":
    return False

  if HashPassword(tokenObj[1]) != os.environ["TOKEN_PASS"]:
    return False

  return True
