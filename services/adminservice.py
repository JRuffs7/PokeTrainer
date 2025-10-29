

from datetime import UTC, datetime, timedelta
import logging
from discord import Embed, Guild, Member, TextChannel
from globals import HelpColor, ShortDateFormat
from models.Server import Server
from services import serverservice
from services.utility import discordservice


eventLogger = logging.getLogger('event')

async def cleanse_helper(guild: Guild, guildMember: Member):
    server = serverservice.GetServer(guild.id)
    update = False
    if not server:
        server = Server(ServerName=guild.name, ServerId=guild.id, LastActivity=datetime.now(UTC).strftime(ShortDateFormat))
        update = True
    if not server.LastActivity:
        server.LastActivity = datetime.now(UTC).strftime(ShortDateFormat)
        update = True
    if update:
        serverservice.UpsertServer(server)
        return

    lastActivity = datetime.strptime(server.LastActivity, ShortDateFormat)
    if (lastActivity + timedelta(days=30)) < datetime.now():
        eventLogger.info(f'Left Server: {server.ServerName} ({server.ServerId}) - {datetime.now(UTC).strftime(ShortDateFormat)}')
        await cleanse_message(discordservice.CreateEmbed(
        'Sorry To Leave',
        'Due to prolonged inactivity on this server, PokeTrainer has decided to remove itself in order to create free space for other servers to invite it. This is due to the limit set by Discord for unverified apps.\n\nYour data **WILL NOT BE DELETED**, and you are free to add PokeTrainer back whenever you wish~\n\nThank you for playing and we hope to see you again.',
        HelpColor), guild, server, guildMember)
        await guild.leave()
        serverservice.DeleteServer(server)

async def cleanse_message(embed: Embed, guild: Guild, server: Server, guildMember: Member):
    if not guild:
        return 
    channel = guild.get_channel(server.ChannelId)
    if not channel:
        channel = next((c for c in guild.text_channels if c.permissions_for(guildMember).send_messages),None)
    if not channel or not isinstance(channel, TextChannel):
        return
    return await channel.send(embed=embed)