import asyncio

import discordbot
from webserver import keep_alive
from dotenv import load_dotenv


async def main():
  await discordbot.StartBot()

load_dotenv()
keep_alive()
asyncio.run(main())
