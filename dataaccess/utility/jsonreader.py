from flask import json


def GetJson(file):
  with open(file, encoding="utf-8") as f:
    return json.load(f)