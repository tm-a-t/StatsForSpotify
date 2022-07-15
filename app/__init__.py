import aiohttp
from fastapi import FastAPI

import config
from app.bot import BotClient
from app.models import User, database
from app.utils import get_spotify
from app.auth import router

app = FastAPI()
app.include_router(router)

bot = BotClient('bot', *config.TELEGRAM_API)
bot.parse_mode = 'html'
bot.app = app


@app.on_event('startup')
async def startup():
    await database.connect()
    app.state.session = aiohttp.ClientSession()
    await bot.run()


@app.on_event('shutdown')
async def shutdown():
    await database.disconnect()
    await app.state.session.close()
