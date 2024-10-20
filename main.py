import asyncio

import discordbot
from logs.logsetup import override_loglevels
from webserver import keep_alive
from dotenv import load_dotenv

async def main():
  await discordbot.StartBot()

load_dotenv('.env')
keep_alive()
override_loglevels()

asyncio.run(main())
