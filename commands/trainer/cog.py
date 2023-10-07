from discord import Member, app_commands
from discord.ext import commands
from discord.user import discord
from commands.views.PokedexView import PokedexView

from globals import ErrorColor, TrainerColor
from models.CustomException import TrainerInvalidException
from services import trainerservice
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
    try:
      result = trainerservice.TryUsePotion(inter.guild_id, inter.user.id,
                                           potion.value)
      if result is None:
        return await discordservice.SendErrorMessage(inter, 'usepotion')

      if result[0]:
        if result[1] > 0:
          return await discordservice.SendMessage(
              inter, 'Health Restored',
              f'{potion.name} used to restore {result[1]} trainer health.',
              TrainerColor, True)
        return await discordservice.SendMessage(
            inter, 'Health Full',
            f'{potion.name} not used because health is already full.',
            TrainerColor, True)
      return await discordservice.SendMessage(
          inter, 'No Healing',
          f'You do not own an {potion.name}s. Please visit the **/shop** to stock up.',
          TrainerColor, True)
    except TrainerInvalidException:
      await discordservice.SendTrainerError(inter)

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
      if images and images.value:
        dexViewer = PokedexView(inter, 1, user if user else inter.user)
        dexViewer.data = pokedex
      else:
        dexViewer = PokedexView(inter, 10, user if user else inter.user)
        dexViewer.data = [
            f"{x['Name']}:sparkles:" if x['Pokemon'].IsShiny else x['Name']
            for x in pokedex
        ]
      await dexViewer.send()

    except TrainerInvalidException:
      await discordservice.SendTrainerError(inter)

  #endregion

  #region STARTER

  @app_commands.command(name="starterkanto", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Bulbasaur", value=1),
      discord.app_commands.Choice(name="Charmander", value=4),
      discord.app_commands.Choice(name="Squirtle", value=7)
  ])
  async def starterkanto(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="starterjohto", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Chikorita", value=152),
      discord.app_commands.Choice(name="Cyndaquil", value=155),
      discord.app_commands.Choice(name="Totodile", value=158)
  ])
  async def starterjohto(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="starterhoenn", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Treecko", value=252),
      discord.app_commands.Choice(name="Torchic", value=255),
      discord.app_commands.Choice(name="Mudkip", value=258)
  ])
  async def starterhoenn(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="startersinnoh",
                        description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Turtwig", value=387),
      discord.app_commands.Choice(name="Chimchar", value=390),
      discord.app_commands.Choice(name="Piplup", value=393)
  ])
  async def startersinnoh(self, inter: discord.Interaction,
                          pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="starterunova", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Snivy", value=495),
      discord.app_commands.Choice(name="Tepig", value=498),
      discord.app_commands.Choice(name="Oshawott", value=501)
  ])
  async def starterunova(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="starterkalos", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Chespin", value=650),
      discord.app_commands.Choice(name="Fennekin", value=653),
      discord.app_commands.Choice(name="Froakie", value=656)
  ])
  async def starterkalos(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="starteralola", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Rowlet", value=722),
      discord.app_commands.Choice(name="Litten", value=725),
      discord.app_commands.Choice(name="Popplio", value=728)
  ])
  async def starteralola(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="startergalar", description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Grookey", value=810),
      discord.app_commands.Choice(name="Scorbunny", value=813),
      discord.app_commands.Choice(name="Sobble", value=816)
  ])
  async def startergalar(self, inter: discord.Interaction,
                         pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  @app_commands.command(name="starterpaldea",
                        description="Start your trainer!")
  @app_commands.choices(pokemon=[
      discord.app_commands.Choice(name="Sprigatito", value=810),
      discord.app_commands.Choice(name="Fuecoco", value=813),
      discord.app_commands.Choice(name="Quaxly", value=816)
  ])
  async def starterpaldea(self, inter: discord.Interaction,
                          pokemon: discord.app_commands.Choice[int]):
    print("STARTER called")
    return await self.start_trainer(inter, pokemon.value)

  async def start_trainer(self, inter: discord.Interaction, pokemonId):
    trainer = trainerservice.GetTrainer(inter.guild_id, inter.user.id)
    if trainer:
      return await inter.response.send_message(
          f"The trainer {inter.user.display_name} already has started to capture Pokemon. This command is only for trainers that have yet to begin their journey.",
          ephemeral=True)

    result = trainerservice.StartTrainer(pokemonId, inter.user.id,
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
        ErrorColor, True)

  #endregion


async def setup(bot: commands.Bot):
  await bot.add_cog(TrainerCommands(bot))
