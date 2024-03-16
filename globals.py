from datetime import datetime
import discord
from flask import json

ShinyOdds: int = 3000
ServerColor: discord.Colour = discord.Colour.blue()
ErrorColor: discord.Colour = discord.Colour.red()
TrainerColor: discord.Colour = discord.Colour.purple()
PokemonColor: discord.Colour = discord.Colour.pink()
EventColor: discord.Colour = discord.Colour.dark_red()
BattleColor: discord.Colour = discord.Colour.dark_orange()
HelpColor: discord.Colour = discord.Colour.default()

PokeballReaction = "🔴"
GreatBallReaction = "🔵"
UltraBallReaction = "🟡"
MasterBallReaction = "🟣"
FightReaction = "⚔️"
MaleSign = "🟦"
FemaleSign = "🟥"
ShinySign = "✨"
Checkmark = "✅"
WarningSign = "⚠️"
DateFormat = '%m/%d/%y %H:%M:%S'
ShortDateFormat = '%m/%d/%Y'

StarterDexIds = [
    range(1, 10),
    range(152, 161),
    range(252, 261),
    range(387, 396),
    range(495, 504),
    range(650, 659),
    range(722, 731),
    range(810, 819),
    range(906, 915)
]


AdminList = [
  215624857793069056
]

eventtimes = [
  datetime.strptime('02:00:00', '%H:%M:%S').time(),
  datetime.strptime('08:00:00', '%H:%M:%S').time(),
  datetime.strptime('14:00:00', '%H:%M:%S').time(),
  datetime.strptime('20:00:00', '%H:%M:%S').time()
]

def to_dict(obj):
  return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

def region_name(id):
  return "Kanto" if id == 1 else "Johto" if id == 2 else "Hoenn" if id == 3 else "Sinnoh" if id == 4 else "Unova" if id == 5 else "Kalos" if id == 6 else "Alola" if id == 7 else "Galar" if id == 8 else "Paldea" if id == 9 else "Voltage"
