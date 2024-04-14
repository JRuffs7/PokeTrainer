import discord

from globals import BlueDiamond, GreenCircle, PokeballReaction, PokemonColor, WhiteCircle
from models.Pokemon import PokemonData
from services import pokemonservice, typeservice
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
		return f'__**TYPE MATCHUP(S)**__\n{self.TypeMatchup()}\n\n__**RARITY MATCHUP**__\n{self.RarityMatchup()}\n\n__**LEVEL ASSISTANCE**__\n{self.GetLevelString()}'

	def TypeMatchup(self):
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

		typeResult = pokemonservice.TypeMatch(self.attackdata.Types, self.defenddata.Types)

		if self.attackdata.Rarity >= 8 and typeResult != -5 and not self.gymbattle:
			return 'Typing for Legendaries/Mythicals/Ultra Beasts against wild Pokemon often does not effect the outcome.'
		
		if self.gymbattle:
			if typeResult == 1 and pokemonservice.IsSpecialPokemon(self.defenddata) and pokemonservice.IsSpecialPokemon(self.attackdata) and len(self.attackdata.Types) == 1:
				expl = passLegRarityString
			elif typeResult == 1 and not pokemonservice.IsSpecialPokemon(self.defenddata):
				expl = passLevelString
			else:
				expl = passString if typeResult >= 2 else failString
			return '\n'.join([self.GetTypeMatchString(), expl])
		else:
			expl = doubleAdvString if typeResult >= 2 else immuneString if typeResult == -5 else doubleDisadvString if typeResult <= -2 else evenString
			return '\n'.join([self.GetTypeMatchString(), expl])

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

	def RarityMatchup(self):
		attackGroup = pokemonservice.RarityGroup(self.attackdata)
		attackGroup = attackGroup % 7 if attackGroup < 10 and self.gymbattle else attackGroup
		defendGroup = pokemonservice.RarityGroup(self.defenddata)
		defendGroup = defendGroup % 7 if defendGroup < 10 and self.gymbattle else defendGroup
		emoji = self.EmojiLookup[-1 if attackGroup < defendGroup else 1 if attackGroup > defendGroup else 0]
		groupStr = f'{emoji} `Attack Rarity {self.attackdata.Rarity} vs Defend Rarity {self.defenddata.Rarity}`\n{emoji} `Group {attackGroup} vs Group {defendGroup}`'

		if self.gymbattle:
			if attackGroup == defendGroup-1 and not pokemonservice.IsSpecialPokemon(self.defenddata):
				return f'{groupStr}\nThe attacking Pokemon **passes** the rarity matchup if they also have level assistance.'
			return f'{groupStr}\nThe attacking Pokemon {"**passes**" if attackGroup >= defendGroup else "**fails**"} the rarity matchup.'
		else:
			return f'{groupStr}\nThis will be a **{"disadvantage" if attackGroup < defendGroup else "advantage" if attackGroup > defendGroup else "neutral"}** rarity matchup.'
		
	def GetLevelString(self):
		attackGroup = pokemonservice.RarityGroup(self.attackdata)
		attackGroup = attackGroup % 7 if attackGroup < 10 else attackGroup
		defendGroup = pokemonservice.RarityGroup(self.defenddata)
		defendGroup = defendGroup % 7 if defendGroup < 10 else defendGroup
		if not self.gymbattle:
			return f'Level advantages are given for the following scenarios:\n```Major Advantage - Attack Level DOUBLE the Defense Level\nMinor Advantage - Attack Level 1.5x the Defense Level```\nThis can also work in reverse with Major/Minor Disadvantage.\n\nIf both Pokemon are under Level 10, only Minor Advantage is given with a level discrepancy of at least 3.\n\n**Potential Health Lost (No Level Assistance): {pokemonservice.WildFight(self.attackdata, self.defenddata, 5 if attackGroup == 1 else 25 if attackGroup == 2 else 35, 5 if defendGroup == 1 else 25 if defendGroup == 2 else 35)}**'
		else:
			defendGroup = pokemonservice.RarityGroup(self.defenddata)
			defendGroup = defendGroup % 7 if defendGroup < 10 else defendGroup
			if defendGroup < 10:
				return f'\nType Assistance:\n- The attacking Pokemon will only gain typing assistance if they are at least Level {23 if defendGroup == 1 else 38 if defendGroup == 2 else 53}\n\nRarity Assistance:\n- The attacking Pokemon will only gain rarity assistance if they are at least Level {19 if defendGroup == 1 else 32 if defendGroup == 2 else 44}'
			else:
				return f'The defending Pokemon will be Level 100, giving no room for level assistance.'