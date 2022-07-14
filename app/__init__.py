import aiohttp
from fastapi import FastAPI

import config
from app.bot import BotClient
from app.models import User
from app.utils import get_spotify
from app.auth import router

app = FastAPI()
app.state.database = User.Meta.database
app.include_router(router)

bot = BotClient('bot', *config.TELEGRAM_API)
bot.parse_mode = 'html'
bot.app = app


@app.on_event('startup')
async def startup():
    database_ = app.state.database
    if not database_.is_connected:
        await database_.connect()

    app.state.session = aiohttp.ClientSession()
    await bot.run()


@app.on_event('shutdown')
async def shutdown():
    database_ = app.state.database
    if database_.is_connected:
        await database_.disconnect()

    await app.state.session.close()
