import discord

from globals import BlueDiamond, GreenCircle, PokeballReaction, PokemonColor, WhiteCircle
from models.Pokemon import PokemonData
from services import battleservice, pokemonservice, typeservice
from services.utility import discordservice


class BattleSimView(discord.ui.View):

	EmojiLookup = {
		1: GreenCircle,
		0: BlueDiamond,
		-1: PokeballReaction,
		-2: WhiteCircle
	}

	def __init__(self, interaction: discord.Interaction, attackData: PokemonData, defendData: PokemonData, gymBattle: bool):
		self.interaction = interaction
		self.attackdata = attackData
		self.defenddata = defendData
		self.gymbattle = gymBattle
		super().__init__(timeout=300)

	async def on_timeout(self):
		await self.message.delete()
		return await super().on_timeout()
    
	async def send(self):
		await self.interaction.followup.send(content="Processing...")
		self.message = await self.interaction.original_response()
		await self.update_message()

	async def update_message(self):
		embed = discordservice.CreateEmbed(
				f"{self.attackdata.Name} VS {self.defenddata.Name} {'Gym Battle' if self.gymbattle else 'Wild Battle'}",
				self.CreateEmbedDesc(), PokemonColor)
		await self.message.edit(content=None, embed=embed, view=self)

	def CreateEmbedDesc(self):
		typeString, typePass = self.TypeMatchup()
		rarityString, rarityPass = self.RarityMatchup()
		return f'__**TYPE MATCHUP(S)**__\n{typeString}\n\n__**RARITY MATCHUP**__\n{rarityString}\n\n__**LEVEL ASSISTANCE**__\n\n{self.GetLevelString(typePass, rarityPass)}'

	def TypeMatchup(self) -> tuple[str, bool]:
		defendGroup = pokemonservice.RarityGroup(self.defenddata)
		defendGroup = defendGroup % 7 if defendGroup < 10 else defendGroup
		passString = 'The attacking Pokemon **passes** the type matchup.'
		passLegRarityString = f'The attacking Pokemon **passes** the type matchup if they also pass the rarity matchup.'
		passLevelString = f'The attacking Pokemon **passes** the type matchup if they also have level assistance and pass the rarity matchup.'
		failString = 'The attacking Pokemon **fails** the type matchup.'
		doubleAdvString = 'This typing matchup will give you a **double advantage**.'
		doubleDisadvString = 'This typing matchup will give you a **double disadvantage**.' 
		evenString = 'This typing matchup will give you no advantage or disadvantage.'
		immuneString = 'The opponent will be immune to your attacks.'

		typeResult = typeservice.TypeMatch(self.attackdata.Types, self.defenddata.Types)

		if self.gymbattle:
			needAssistance: bool = False
			if typeResult == 1 and pokemonservice.IsLegendaryPokemon(self.defenddata) and pokemonservice.IsLegendaryPokemon(self.attackdata) and len(self.attackdata.Types) == 1:
				expl = passLegRarityString
			elif typeResult == 1 and not pokemonservice.IsLegendaryPokemon(self.defenddata):
				needAssistance = True
				expl = passLevelString
			elif typeResult >= 2:
				expl = passString
			else:
				expl = failString
			return ('\n'.join([self.GetTypeMatchString(), expl]), needAssistance)
		else:
			expl = doubleAdvString if typeResult >= 2 else immuneString if typeResult == -5 else doubleDisadvString if typeResult <= -2 else evenString
			return ('\n'.join([self.GetTypeMatchString(), expl]), True)

	def GetTypeMatchString(self):
		if len(self.attackdata.Types) == 1 and len(self.defenddata.Types) == 1:
			fight = typeservice.TypeWeakness(self.attackdata.Types[0].lower(), self.defenddata.Types[0].lower())
			return f'{self.EmojiLookup[fight]} `{self.attackdata.Types[0]} vs {self.defenddata.Types[0]}`'
			
		elif len(self.attackdata.Types) == 1 and len(self.defenddata.Types) == 2:
			fight = typeservice.TypeWeakness(self.attackdata.Types[0].lower(), self.defenddata.Types[0].lower())
			fight2 = typeservice.TypeWeakness(self.attackdata.Types[0].lower(), self.defenddata.Types[1].lower())
			res1Str = f'{self.EmojiLookup[fight]} `{self.attackdata.Types[0]} vs {self.defenddata.Types[0]}`'
			res2Str = f'{self.EmojiLookup[fight2]} `{self.attackdata.Types[0]} vs {self.defenddata.Types[1]}`'
			return '\n'.join([res1Str, res2Str])
			
		elif len(self.attackdata.Types) == 2 and len(self.defenddata.Types) == 1:
			fight = typeservice.TypeWeakness(self.attackdata.Types[0].lower(), self.defenddata.Types[0].lower())
			fight2 = typeservice.TypeWeakness(self.attackdata.Types[1].lower(), self.defenddata.Types[0].lower())
			res1Str = f'{self.EmojiLookup[fight]} `{self.attackdata.Types[0]} vs {self.defenddata.Types[0]}`'
			res2Str = f'{self.EmojiLookup[fight2]} `{self.attackdata.Types[1]} vs {self.defenddata.Types[0]}`'
			return '\n'.join([res1Str, res2Str])

		else:
			fightA1 = typeservice.TypeWeakness(self.attackdata.Types[0].lower(), self.defenddata.Types[0].lower())
			fightA2 = typeservice.TypeWeakness(self.attackdata.Types[0].lower(), self.defenddata.Types[1].lower())
			fightB1 = typeservice.TypeWeakness(self.attackdata.Types[1].lower(), self.defenddata.Types[0].lower())
			fightB2 = typeservice.TypeWeakness(self.attackdata.Types[1].lower(), self.defenddata.Types[1].lower())
			res1Str = f'{self.EmojiLookup[fightA1]} `{self.attackdata.Types[0]} vs {self.defenddata.Types[0]}`'
			res2Str = f'{self.EmojiLookup[fightA2]} `{self.attackdata.Types[0]} vs {self.defenddata.Types[1]}`'
			res3Str = f'{self.EmojiLookup[fightB1]} `{self.attackdata.Types[1]} vs {self.defenddata.Types[0]}`'
			res4Str = f'{self.EmojiLookup[fightB2]} `{self.attackdata.Types[1]} vs {self.defenddata.Types[1]}`'
			return '\n'.join([res1Str, res2Str, res3Str, res4Str])

	def RarityMatchup(self) -> tuple[str, bool]:
		attackGroup = pokemonservice.RarityGroup(self.attackdata)
		attackGroup = attackGroup if attackGroup == 10 and self.gymbattle else attackGroup % 7
		defendGroup = pokemonservice.RarityGroup(self.defenddata)
		defendGroup = defendGroup if defendGroup == 10 and self.gymbattle else defendGroup % 7
		emoji = self.EmojiLookup[-1 if attackGroup < defendGroup else 1 if attackGroup > defendGroup else 0]
		groupStr = f'{emoji} `Attack Rarity {self.attackdata.Rarity} vs Defend Rarity {self.defenddata.Rarity}`\n{emoji} `Group {attackGroup} vs Group {defendGroup}`'

		if self.gymbattle:
			if attackGroup == defendGroup-1 and not pokemonservice.IsLegendaryPokemon(self.defenddata):
				return (f'{groupStr}\nThe attacking Pokemon **passes** the rarity matchup if they also have level assistance.', True)
			return (f'{groupStr}\nThe attacking Pokemon {"**passes**" if attackGroup >= defendGroup else "**fails**"} the rarity matchup.', False)
		else:
			return (f'{groupStr}\nThis will be a **{"disadvantage" if attackGroup < defendGroup else "advantage" if attackGroup > defendGroup else "neutral"}** rarity matchup.', True)
		
	def GetLevelString(self, typeAssist: bool, rarityAssist: bool):
		attackGroup = pokemonservice.RarityGroup(self.attackdata)
		attackGroup = attackGroup if attackGroup == 10 and self.gymbattle else attackGroup % 7
		defendGroup = pokemonservice.RarityGroup(self.defenddata)
		defendGroup = defendGroup if attackGroup == 10 and self.gymbattle else defendGroup % 7
		if not self.gymbattle:
			return f'Level advantages are given for the following scenarios:\n```Major Advantage - Attack Level > Defense Level x 2\nMinor Advantage - Attack Level > Defense Level x 1.5```\nThis can also work in reverse with Major/Minor Disadvantage.\n\nIf both Pokemon are under Level 10, only Minor Advantage is given with a level discrepancy of at least 3.\n\n**Potential Health Lost (No Level Assistance): {battleservice.WildFight(self.attackdata, self.defenddata, 5 if attackGroup == 1 else 25 if attackGroup == 2 else 35, 5 if defendGroup == 1 else 25 if defendGroup == 2 else 35)}**'
		else:
			defendGroup = pokemonservice.RarityGroup(self.defenddata)
			defendGroup = defendGroup % 7 if defendGroup < 10 else defendGroup
			if defendGroup < 10:
				typeAssistStr = f'Type Assistance:\n- The attacking Pokemon will only gain typing assistance if they are Level {23 if defendGroup == 1 else 38 if defendGroup == 2 else 53}+'
				rarityAssistStr = f'Rarity Assistance:\n- The attacking Pokemon will only gain rarity assistance if they are Level {19 if defendGroup == 1 else 32 if defendGroup == 2 else 44}+'
				if typeAssist and rarityAssist:
					return f'{typeAssistStr}\n\n{rarityAssistStr}'
				elif typeAssist:
					return f'{typeAssistStr}'
				elif rarityAssist:
					return f'{rarityAssistStr}'
				else:
					return 'This matchup does not qualify for any Level Assistance.'
			else:
				return f'The defending Pokemon will be Level 100, giving no room for level assistance.'