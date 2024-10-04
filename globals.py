from datetime import datetime
import discord
from flask import json

ShinyOdds: int = 3000
GreatShinyOdds: int = 2000
SuperShinyOdds: int = 1000
ServerColor: discord.Colour = discord.Colour.blue()
ErrorColor: discord.Colour = discord.Colour.red()
SuccessColor: discord.Colour = discord.Colour.green()
TrainerColor: discord.Colour = discord.Colour.purple()
PokemonColor: discord.Colour = discord.Colour.pink()
EventColor: discord.Colour = discord.Colour.dark_red()
BattleColor: discord.Colour = discord.Colour.dark_orange()
HelpColor: discord.Colour = discord.Colour.default()
TradeColor: discord.Colour = discord.Colour.yellow()

PokeballReaction = "🔴"
GreatBallReaction = "🔵"
UltraBallReaction = "🟡"
MasterBallReaction = "🟣"
FightReaction = "⚔️"
MaleSign = "🟦"
FemaleSign = "🟥"
ShinySign = "✨"
Dexmark = "✅"
Formmark = "☑️"
Incomplete = "❌"
WarningSign = "⚠️"
GreenCircle = "🟢"
BlueDiamond = "🔹"
WhiteCircle = "⚪"
DateFormat = '%m/%d/%y %H:%M:%S'
ShortDateFormat = '%m/%d/%Y'

botImage = 'https://imgur.com/MIfTed5.png'
discordLink = 'https://discord.com/invite/W9T4K7fyYu'
topggLink = 'https://top.gg/bot/1151657435073875988'

AdminList = [
  215624857793069056
]

eventtimes = [
  datetime.strptime('02:00:00', '%H:%M:%S').time(),
  datetime.strptime('08:00:00', '%H:%M:%S').time(),
  datetime.strptime('14:00:00', '%H:%M:%S').time(),
  datetime.strptime('20:00:00', '%H:%M:%S').time()
]

freemasterball = datetime(2024,4,26)

def to_dict(obj):
  return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

def region_name(id):
  return "Kanto" if id == 1 else "Johto" if id == 2 else "Hoenn" if id == 3 else "Sinnoh" if id == 4 else "Unova" if id == 5 else "Kalos" if id == 6 else "Alola" if id == 7 else "Galar" if id == 8 else "Paldea" if id == 9 else "Voltage"
