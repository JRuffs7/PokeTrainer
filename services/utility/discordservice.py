import discord
from discord import Embed, Interaction

import discordbot
from globals import (
    ErrorColor,
    FightReaction,
    GetJson,
    GreatBallReaction,
    PokeballReaction,
    PokemonSpawnColor,
    UltraBallReaction,
)
from models.Pokemon import SpawnPokemon
from services import helpservice, pokemonservice


async def SendErrorMessage(interaction, command):
  helpObj = helpservice.BuildCommandHelp(
      command, interaction.user.guild_permissions.administrator)
  if helpObj:
    return await interaction.response.send_message(embed=CreateEmbed(
        f'{helpObj.Name} Command Usage', helpObj.HelpString, ErrorColor),
                                            ephemeral=True)
  return await interaction.response.send_message(embed=CreateEmbed(
        f'{command} Command Usage', "You do not have permission to use this command. Inquire a server administrator for further details.", ErrorColor),
                                            ephemeral=True)


async def SendMessage(interaction, title, desc, color, eph=False):
  return await interaction.response.send_message(embed=CreateEmbed(
      title, desc, color),
                                          ephemeral=eph)


async def SendEmbed(interaction, embed, eph=False):
  return await interaction.response.send_message(embed=embed, ephemeral=eph)


async def SendDM(inter, title, desc, color):
  return await inter.user.send(embed=CreateEmbed(title, desc, color))


async def SendDMs(inter, embedList):
  return await inter.user.send(embeds=embedList)


async def EditMessage(message, newEmbed, color):
  newEmbed.color = color
  return await message.edit(embed=newEmbed)

async def DeleteMessage(serverId, channelId, messageId):
  bot = discordbot.GetBot()
  guild = bot.get_guild(serverId)
  if guild:
    channel = guild.get_channel(channelId)
    if channel:
      try:
        return await (await channel.fetch_message(messageId)).delete()
      except:
        print(f"SERVER: {serverId} deleted last spawn already")
        return


async def SendMessageNoInteraction(serverId, channelId, message):
  bot = discordbot.GetBot()
  guild = bot.get_guild(serverId)
  if guild:
    channel = guild.get_channel(channelId)
    if channel and not isinstance(channel,
                                  discord.ForumChannel) and not isinstance(
                                      channel, discord.CategoryChannel):
      await channel.send(message)


async def SendPokemon(guildid,
                      channelid,
                      pokemon: SpawnPokemon,
                      test: bool = False):
  pkmn = pokemonservice.GetPokemonById(pokemon.Pokemon_Id)
  if not pkmn:
    print(f'Error spawning Pokemon with ID: {pokemon.Pokemon_Id}')
    return

  embed = CreateEmbed(
      f"{pkmn.Name}{pokemon.GetNameEmojis()}",
      f"Height: {pokemon.Height}\nWeight: {pokemon.Weight}", PokemonSpawnColor)
  embed.set_image(url=pkmn.GetImage(pokemon.IsShiny, pokemon.IsFemale))
  bot = discordbot.GetBot()
  guild = bot.get_guild(guildid)
  if guild:
    channel = guild.get_channel(channelid)
    if channel and not isinstance(channel,
                                  discord.ForumChannel) and not isinstance(
                                      channel, discord.CategoryChannel):
      message = await channel.send(embed=embed)
      if not test:
        await message.add_reaction(PokeballReaction)
        await message.add_reaction(GreatBallReaction)
        await message.add_reaction(UltraBallReaction)
        await message.add_reaction(FightReaction)
      return message
  return None


async def SendTrainerError(interaction):
  return await interaction.response.send_message(embed=CreateEmbed(
      "Trainer Missing!",
      "You have not started your PokeTrainer journey yet! To do so, use one of the **/starter** commands. Please use **/help** for more explanation on how PokeTrainer is used.",
      ErrorColor),
                                          ephemeral=True)


async def SendServerError(interaction):
  return await interaction.response.send_message(embed=CreateEmbed(
      "Server Not Registered",
      "This server has not been registered with PokeTrainer! To do so, have an administrator run the **/start *percent*** command. Please use **/help** for more explanation on how PokeTrainer is used.",
      ErrorColor),
                                          ephemeral=True)


async def SendCommandResponse(interaction: Interaction, filename: str, command: str, responseInd: int, color, params: list=[], eph: bool=False):
  response = GetJson(filename)[command][responseInd]
  return await interaction.response.send_message(embed=CreateEmbed(
      response["Title"], response["Body"].format(*params), color), ephemeral=eph)


def CreateEmbed(title, desc, color):
  return Embed(title=title, description=desc, color=color)
