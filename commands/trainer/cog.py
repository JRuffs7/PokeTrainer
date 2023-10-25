from typing import List
from discord import Member, app_commands
from discord.ext import commands
from discord.user import discord
from commands.views.PokedexView import PokedexView
from commands.views.TeamSelectorView import TeamSelectorView

from globals import ErrorColor, TrainerColor
from models.CustomException import TrainerInvalidException
from services import trainerservice, pokemonservice
from services.utility import discordservice


class TrainerCommands(commands.Cog, name="TrainerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="trainerinfo",
                        description="Displays trainer info.")
  async def trainerinfo(self,
                        interaction: discord.Interaction,
                        member: Member | None = None):
    print("TRAINER INFO called")
    targetUser = member if member else interaction.user
    trainer = trainerservice.GetTrainer(interaction.guild_id, targetUser.id)

    embed = discordservice.CreateEmbed(
        f"{targetUser.display_name}'s Trainer Info", trainer if trainer else
        "This user does not have a registered trainer for this server. To create a trainer, react and catch a spawned Pokemon, or use the **~starter** command.",
        TrainerColor)
    if trainer:
      embed.set_thumbnail(url=targetUser.display_avatar.url)
    await discordservice.SendEmbed(interaction, embed)

  @app_commands.command(name="usepotion",
                        description="Use a potion to restore trainer health.")
  @app_commands.choices(potion=[
      discord.app_commands.Choice(name="Potion", value=1),
      discord.app_commands.Choice(name="Super Potion", value=2),
      discord.app_commands.Choice(name="Hyper Potion", value=3),
      discord.app_commands.Choice(name="Max Potion", value=4)
  ])
  async def usepotion(self, inter: discord.Interaction,
                      potion: app_commands.Choice[int]):
    result = trainerservice.TryUsePotion(inter.guild_id, inter.user.id,
                                          potion.value)
    if result is None:
      return await discordservice.SendErrorMessage(inter, 'usepotion')

    if result[0]:
      if result[1] > 0:
        return await discordservice.SendMessage(
            inter, 'Health Restored',
            f'{potion.name} used to restore {result[1]} trainer health.',
            TrainerColor)
      return await discordservice.SendMessage(
          inter, 'Health Full',
          f'{potion.name} not used because health is already full.',
          TrainerColor)
    return await discordservice.SendMessage(
        inter, 'No Healing',
        f'You do not own an {potion.name}s. Please visit the **/shop** to stock up.',
        TrainerColor)

  @app_commands.command(name="inventory",
                        description="Displays your current inventory.")
  async def inventory(self, inter: discord.Interaction):
    print("INVENTORY called")
    try:
      items = trainerservice.GetInventory(inter.guild_id, inter.user.id)
      pkblList = items[1]
      ptnList = items[2]
      newline = '\n'

      pokeballString = f"__Pokeballs__\n{newline.join([f'{i}: {pkblList[i]}' for i in pkblList])}"
      potionString = f"__Potions__\n{newline.join([f'{i}: {ptnList[i]}' for i in ptnList])}"
      embed = discordservice.CreateEmbed(
          f"{inter.user.display_name}'s Inventory",
          f"${items[0]}\n\n{pokeballString}\n\n{potionString}", TrainerColor)
      return await discordservice.SendEmbed(inter, embed, True)
    except TrainerInvalidException:
      await discordservice.SendTrainerError(inter)

  #region TEAM

  async def pokemon_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    data = []
    pkmnList = [p.Name for p in trainerservice.GetUniquePokemon(inter.guild_id, inter.user.id)]
    pkmnList.sort()
    for pkmn in pkmnList:
      if current.lower() in pkmn.lower():
        data.append(app_commands.Choice(name=pkmn, value=pkmn.lower()))
      if len(data) == 25:
        break
    return data

  @app_commands.command(name="modifyteam",
                        description="Add or substitute a Pokemon to a team slot.")
  @app_commands.autocomplete(pokemon=pokemon_autocomplete)
  async def modifyteam(self, inter: discord.Interaction,
                    pokemon: str):
    print('MODIFY TEAM called')
    try:
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      result = trainerservice.GetPokedexList(inter.guild_id, inter.user.id, None, None)
      result = [x for x in result if x.Name.lower() == pokemon.lower() and x.Pokemon.Id not in trainer.Team]
      if not result:
        return await discordservice.SendMessage(inter, 'Invalid Pokemon', f'You do not own any Pokemon with the name {pokemon}', ErrorColor)

      teamSelect = TeamSelectorView(
        inter,
        trainerservice.GetTrainerTeam(inter.guild_id, inter.user.id),
        result)
      await teamSelect.send()
    except TrainerInvalidException:
      await discordservice.SendTrainerError(inter)

  #endregion

  #region POKEDEX

  @app_commands.command(name="pokedex",
                        description="Displays your current Pokedex.")
  @app_commands.choices(images=[
      discord.app_commands.Choice(name="Yes", value=1),
      discord.app_commands.Choice(name="No", value=0)
  ])
  @app_commands.choices(order=[
      discord.app_commands.Choice(name="Default", value="default"),
      discord.app_commands.Choice(name="Height", value="height"),
      discord.app_commands.Choice(name="National Dex", value="dex"),
      discord.app_commands.Choice(name="Name", value="name"),
      discord.app_commands.Choice(name="Weight", value="weight")
  ])
  @app_commands.choices(shiny=[
      discord.app_commands.Choice(name="All", value=1),
      discord.app_commands.Choice(name="Shiny Only", value=2),
      discord.app_commands.Choice(name="Shiny First", value=3)
  ])
  async def pokedex(self, inter: discord.Interaction,
                    images: app_commands.Choice[int] | None,
                    order: app_commands.Choice[str] | None,
                    shiny: app_commands.Choice[int] | None,
                    user: discord.Member | None):
    print("POKEDEX called")
    try:
      pokedex = trainerservice.GetPokedexList(
          inter.guild_id, user.id if user else inter.user.id,
          order.value if order else None, shiny.value if shiny else None)
      numUnique = len(trainerservice.GetUniquePokemon(inter.guild_id, user.id if user else inter.user.id))
      numPkmn = pokemonservice.GetPokemonCount()
      if images and images.value:
        dexViewer = PokedexView(inter, 1, user if user else inter.user, f"{user.display_name if user else inter.user.display_name}'s Pokedex ({numUnique}/{numPkmn})")
      else:
        dexViewer = PokedexView(inter, 10, user if user else inter.user, f"{user.display_name if user else inter.user.display_name}'s Pokedex ({numUnique}/{numPkmn})")
      
      dexViewer.data = [p for p in pokedex ]
      await dexViewer.send()
    except TrainerInvalidException:
      await discordservice.SendTrainerError(inter)

  #endregion

  #region STARTER

  async def region_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    regions = ['Kanto','Johto','Hoenn','Sinnoh','Unova','Kalos','Alola','Galar','Paldea']
    choices = []
    for i in range(len(regions)):
      if current.lower() in regions[i].lower():
        choices.append(app_commands.Choice(name=regions[i],value=i+1))
    return choices
  
  async def starter_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[int]]:
    starters = [ 
      {'Region':1,'Name':'Bulbasaur','Value':1},
      {'Region':1,'Name':'Charmander','Value':4},
      {'Region':1,'Name':'Squirtle','Value':7},
      {'Region':2,'Name':'Chikorita','Value':152},
      {'Region':2,'Name':'Cyndaquil','Value':155},
      {'Region':2,'Name':'Totodile','Value':158},
      {'Region':3,'Name':'Treecko','Value':252},
      {'Region':3,'Name':'Torchic','Value':255},
      {'Region':3,'Name':'Mudkip','Value':258},
      {'Region':4,'Name':'Turtwig','Value':387},
      {'Region':4,'Name':'Chimchar','Value':390},
      {'Region':4,'Name':'Piplup','Value':393},
      {'Region':5,'Name':'Snivy','Value':495},
      {'Region':5,'Name':'Tepig','Value':498},
      {'Region':5,'Name':'Oshawott','Value':501},
      {'Region':6,'Name':'Chespin','Value':650},
      {'Region':6,'Name':'Fenniken','Value':653},
      {'Region':6,'Name':'Froakie','Value':656},
      {'Region':7,'Name':'Rowlet','Value':722},
      {'Region':7,'Name':'Litten','Value':725},
      {'Region':7,'Name':'Popplio','Value':728},
      {'Region':8,'Name':'Grookey','Value':810},
      {'Region':8,'Name':'Scorbunny','Value':813},
      {'Region':8,'Name':'Sobble','Value':816},
      {'Region':9,'Name':'Sprigatito','Value':906},
      {'Region':9,'Name':'Fuecoco','Value':909},
      {'Region':9,'Name':'Quaxly','Value':912}
    ]
    region = int(inter.namespace['region'])
    choices = []
    if not region:
      choices.append(app_commands.Choice(name='Choose a region',value=0))
    else:
      for st in starters:
        if current.lower() in st['Name'].lower() and st['Region'] == region:
          choices.append(app_commands.Choice(name=st['Name'],value=st['Value']))
    return choices

  @app_commands.command(name="starter",
                        description="Choose a region and Pokemon to start your trainer!")
  @app_commands.autocomplete(region=region_autocomplete,pokemon=starter_autocomplete)
  async def starter(self, inter: discord.Interaction, region: int, pokemon: int):
    print("STARTER called")
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      return await inter.response.send_message(
          f"The trainer {inter.user.display_name} already has started to capture Pokemon. This command is only for trainers that have yet to begin their journey.",
          ephemeral=True)

    result = trainerservice.StartTrainer(pokemon, inter.user.id,
                                         inter.guild_id)
    if result:
      embed = discordservice.CreateEmbed(
          "Trainer Created!",
          f"Starter: {result[1].Name} {':female_sign:' if result[0].OwnedPokemon[0].IsFemale else ':male_sign:'}\nStarting Money: ${result[0].Money}",
          TrainerColor)
      embed.set_image(
          url=result[1].GetImage(result[2].IsShiny, result[2].IsFemale))
      return await discordservice.SendEmbed(inter, embed)
    return await discordservice.SendMessage(
        inter, "Unable to Create Trainer",
        "Something went wrong while starting your journey. Maybe there weren't any of the Pokemon you chose? Nah, must have been something else...",
        ErrorColor)

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
