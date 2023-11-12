import discord
from flask import json

PokeApiUrl: str = 'https://pokeapi.co/api/v2'
ShinyOdds: int = 3000
ServerDetailColor: discord.Colour = discord.Colour.blue()
ErrorColor: discord.Colour = discord.Colour.red()
TrainerColor: discord.Colour = discord.Colour.purple()
PokemonColor: discord.Colour = discord.Colour.pink()
PokemonSpawnColor: discord.Colour = discord.Colour.light_embed()
PokemonCaughtColor: discord.Colour = discord.Colour.green()
ShopSuccessColor: discord.Colour = discord.Colour.dark_green()
ShopFailColor: discord.Colour = discord.Colour.dark_red()
HelpColor: discord.Colour = discord.Colour.default()

PokeballReaction = "🔴"
GreatBallReaction = "🔵"
UltraBallReaction = "🟡"
MasterBallReaction = "🟣"
FightReaction = "⚔️"
MaleSign = "🟦"
FemaleSign = "🟥"
ShinySign = "✨"

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


def to_dict(obj):
  return json.loads(json.dumps(obj, default=lambda o: o.__dict__))
