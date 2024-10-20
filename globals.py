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
BattleColor: discord.Colour = discord.Colour.dark_orange()
HelpColor: discord.Colour = discord.Colour.default()
TradeColor: discord.Colour = discord.Colour.yellow()

MaleSign = "🟦"
FemaleSign = "🟥"
ShinySign = "✨"
Dexmark = "✅"
Formmark = "☑️"
Incomplete = "❌"
DateFormat = '%m/%d/%y %H:%M:%S'
ShortDateFormat = '%m/%d/%Y'

botImage = 'https://imgur.com/MIfTed5.png'
discordLink = 'https://discord.gg/W9T4K7fyYu'
topggLink = 'https://top.gg/bot/1151657435073875988'
discordbotlistLink = 'https://discordbotlist.com/servers/poketrainer/upvote'

AdminList = [
  215624857793069056
]

freemasterball = datetime(2024,10,4)

def to_dict(obj):
  return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

def region_name(id: int):
  return "Kanto" if id == 1 else "Johto" if id == 2 else "Hoenn" if id == 3 else "Sinnoh" if id == 4 else "Unova" if id == 5 else "Kalos" if id == 6 else "Alola" if id == 7 else "Galar" if id == 8 else "Paldea" if id == 9 else "Voltage"
