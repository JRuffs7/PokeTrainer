from typing import List
from discord import Member, app_commands
from discord.ext import commands
from discord.user import discord
from commands.views.PokedexView import PokedexView
from commands.views.TeamSelectorView import TeamSelectorView
from commands.views.ReleasePokemonView import ReleasePokemonView

from globals import ErrorColor, TrainerColor
from services import trainerservice, pokemonservice, itemservice, gymservice
from services.utility import discordservice


class TrainerCommands(commands.Cog, name="TrainerCommands"):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  #region Info

  @app_commands.command(name="trainer",
                        description="Displays trainer info.")
  async def trainer(self,
                        interaction: discord.Interaction,
                        member: Member | None = None):
    print("TRAINER called")
    targetUser = member if member else interaction.user
    trainer = trainerservice.GetTrainer(interaction.guild_id, targetUser.id)
    if not trainer:
      return await discordservice.SendTrainerError(interaction)

    embed = discordservice.CreateEmbed(f"{targetUser.display_name}'s Trainer Info", trainer, TrainerColor)
    embed.set_thumbnail(url=targetUser.display_avatar.url)
    await discordservice.SendEmbed(interaction, embed)

  async def autofill_usepotion(self, inter: discord.Interaction, current: str):
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      ptnList = [itemservice.GetPotion(p) for p in trainer.PotionList]
      ptnList.sort(key=lambda x: x.Id)
      for ptn in ptnList:
        if current.lower() in ptn.Name.lower() and ptn.Name not in [i.name for i in data]:
          data.append(app_commands.Choice(name=ptn.Name, value=ptn.Id))
        if len(data) == 25:
          break
    return data

  @app_commands.command(name="usepotion",
                        description="Use a potion to restore trainer health.")
  @app_commands.autocomplete(potion=autofill_usepotion)
  async def usepotion(self, inter: discord.Interaction,
                      potion: int):
    print("USE POTION called")
    try:
      trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
      ptn = itemservice.GetPotion(potion)
      if not trainer or not ptn:
        return await discordservice.SendTrainerError(inter)
      
      result = trainerservice.TryUsePotion(trainer, ptn)
      if result is None:
        return await discordservice.SendErrorMessage(inter, 'usepotion')

      if result[0]:
        if result[1] > 0:
          return await discordservice.SendMessage(
              inter, 'Health Restored',
              f'{ptn.Name} used to restore {result[1]} trainer health.',
              TrainerColor)
        return await discordservice.SendMessage(
            inter, 'Health Full',
            f'{ptn.Name} not used because health is already full.',
            TrainerColor)
      return await discordservice.SendMessage(
          inter, 'No Healing',
          f'You do not own an {ptn.Name}s. Please visit the **/shop** to stock up.',
          TrainerColor)
    except Exception as e:
      print(f"{e}")

  @app_commands.command(name="inventory",
                        description="Displays your current inventory.")
  async def inventory(self, inter: discord.Interaction):
    print("INVENTORY called")
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not trainer:
      return await discordservice.SendTrainerError(inter)
    
    items = trainerservice.GetInventory(trainer)
    pkblList = items[1]
    ptnList = items[2]
    newline = '\n'

    pokeballString = f"__Pokeballs__\n{newline.join([f'{i}: {pkblList[i]}' for i in pkblList])}"
    potionString = f"__Potions__\n{newline.join([f'{i}: {ptnList[i]}' for i in ptnList])}"
    embed = discordservice.CreateEmbed(
        f"{inter.user.display_name}'s Inventory",
        f"${items[0]}\n\n{pokeballString}\n\n{potionString}", TrainerColor)
    return await discordservice.SendEmbed(inter, embed, True)
      
  #endregion

  #region TEAM

  async def pokemon_autocomplete(self, inter: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    data = []
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      pkmnList = list(set([p.Name for p in trainer.OwnedPokemon if p.Id not in trainer.Team]))
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
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not trainer:
      return await discordservice.SendTrainerError(inter)
    
    result = [x for x in trainer.OwnedPokemon if x.Name.lower() == pokemon.lower()]
    if not result:
      return await discordservice.SendMessage(inter, 'Invalid Pokemon', f'You do not own any Pokemon with the name {pokemon}', ErrorColor)

    teamSelect = TeamSelectorView(
      inter,
      [next((p for p in trainer.OwnedPokemon if t and p.Id == t), None) for t in trainer.Team],
      result)
    await teamSelect.send()

  @app_commands.command(name="myteam",
                        description="View your current team.")
  async def myteam(self, inter: discord.Interaction):
    print("MY TEAM called")
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not trainer:
      return await discordservice.SendTrainerError(inter)

    teamViewer = PokedexView(inter, 1, inter.user, f"{inter.user.display_name}'s Battle Team")
    teamViewer.data = trainerservice.GetTeam(trainer)
    await teamViewer.send()

  @app_commands.command(name="gymbattle",
                        description="Battle each gym leader from every region.")
  async def gymbattle(self, inter: discord.Interaction):
    print("GYM BATTLE called")
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not trainer:
      return await discordservice.SendTrainerError(inter)
    
    gymleader = gymservice.GetNextTrainerGym(trainer)
    if not gymleader:
      return await discordservice.SendMessage(
        inter, 
        "No Battles Left",
        "Congratulations! You have beaten all the gym leaders! Check out your badges by using **/badges**.",
        TrainerColor)
    

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
    trainer = trainerservice.GetTrainer(inter.guild_id, user.id if user else inter.user.id)
    if not trainer:
      return await discordservice.SendTrainerError(inter)
    
    numUnique = len(set([p.Pokemon.Pokemon_Id for p in trainer.OwnedPokemon]))
    numPkmn = pokemonservice.GetPokemonCount()
    if images and images.value:
      dexViewer = PokedexView(inter, 1, user if user else inter.user, f"{user.display_name if user else inter.user.display_name}'s Pokedex ({numUnique}/{numPkmn})")
    else:
      dexViewer = PokedexView(inter, 10, user if user else inter.user, f"{user.display_name if user else inter.user.display_name}'s Pokedex ({numUnique}/{numPkmn})")
    dexViewer.data = trainerservice.GetPokedexList(trainer, order.value if order else None, shiny.value if shiny else None)
    await dexViewer.send()
      

  @app_commands.command(name="release",
                        description="Choose a Pokemon to release.")
  @app_commands.autocomplete(pokemon=pokemon_autocomplete)
  async def release(self, inter: discord.Interaction,
                    pokemon: str):
    print('RELEASE called')
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if not trainer:
      return await discordservice.SendTrainerError(inter)
    
    result = [x for x in trainer.OwnedPokemon if x.Name.lower() == pokemon.lower()]
    if not result:
      return await discordservice.SendMessage(inter, 'Invalid Pokemon', f'You do not own any Pokemon with the name {pokemon}', ErrorColor)

    releaseSelect = ReleasePokemonView(
      inter,
      result)
    await releaseSelect.send()

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

    trainer = trainerservice.StartTrainer(pokemon, inter.user.id,
                                         inter.guild_id)
    if trainer:
      embed = discordservice.CreateEmbed(
          "Trainer Created!",
          f"Starter: {trainer.OwnedPokemon[0].GetNameString()}\nStarting Money: ${trainer.Money}\nStarting Pokeballs: 5",
          TrainerColor)
      embed.set_image(url=trainer.OwnedPokemon[0].Sprite)
      return await discordservice.SendEmbed(inter, embed)
    return await discordservice.SendMessage(
        inter, "Unable to Create Trainer",
        "Something went wrong while starting your journey. Maybe there weren't any of the Pokemon you chose? Nah, must have been something else...",
        ErrorColor)

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
