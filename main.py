import asyncio
import sys

import discordbot
from logs.logsetup import override_loglevels
from webserver import keep_alive
from dotenv import load_dotenv


async def main():
  await discordbot.StartBot()

if len(sys.argv) == 2 and sys.argv[1] == 'prodbuild':
  load_dotenv('.env')
else:
  load_dotenv('.env.local')
keep_alive()
override_loglevels()

asyncio.run(main())
