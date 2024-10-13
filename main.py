import asyncio
from datetime import UTC, datetime, timedelta
import sys

import discordbot
from logs.logsetup import override_loglevels
from webserver import keep_alive
from dotenv import load_dotenv
from globals import eventtimes

#Comment
async def main(key: str):
  await discordbot.StartBot(key)

key = ''
with open("DiscordBotToken.txt") as keyFile:
  key = keyFile.read()
if len(sys.argv) == 2 and sys.argv[1] == 'prodbuild':
  load_dotenv('.env')
else:
  load_dotenv('.env.local')
  eventtimes.clear()
  eventtimes.append((datetime.now(UTC)+timedelta(seconds=15)).time())
keep_alive()
override_loglevels()

asyncio.run(main(key))
