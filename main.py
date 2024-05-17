import asyncio
from datetime import UTC, datetime, timedelta
import sys

import discordbot
from logs.logsetup import override_loglevels
from webserver import keep_alive
from dotenv import load_dotenv
from globals import DateFormat, eventtimes


async def main():
  await discordbot.StartBot()

if len(sys.argv) == 2 and sys.argv[1] == 'prodbuild':
  load_dotenv('.env')
else:
  load_dotenv('.env.local')
  eventtimes.clear()
  eventtimes.append((datetime.now(UTC)+timedelta(seconds=15)).time())
keep_alive()
override_loglevels()

asyncio.run(main())
