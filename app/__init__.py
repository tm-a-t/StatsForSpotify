import secrets

import aiohttp
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

import config
from app.bot import BotClient
from app.models import User
from app.utils import get_spotify

app = FastAPI()
app.state.database = User.Meta.database

bot = BotClient('bot', *config.TELEGRAM_API)
bot.parse_mode = 'html'
bot.app = app

auth_state_data = {}


@app.get('/')
async def authorize_spotify(request: Request, id: int, first_name: str, last_name: str, photo_url: str, username: str):
    # todo: check authorization (https://core.telegram.org/widgets/login#checking-authorization)
    state = secrets.token_urlsafe(16)
    auth_state_data[state] = dict(
        id=id, first_name=first_name, last_name=last_name, username=username, photo_url=photo_url
    )

    redirect_uri = request.url_for('spotify_callback')
    spotify = get_spotify(app.state.session, redirect_uri, state=state)
    return RedirectResponse(spotify.auth.get_authorize_url())


@app.get('/callback')
async def spotify_callback(request: Request, code: str, state: str):
    redirect_uri = request.url_for('spotify_callback')
    spotify = get_spotify(app.state.session, redirect_uri)
    token = await spotify.auth.get_token_from_code(code)
    user = await User.objects.get_or_none(id=auth_state_data[state]['id'])
    if user is None:
        await User.objects.create(
            **auth_state_data[state],
            refresh_token=token.refresh_token
        )
    auth_state_data.pop(state)
    return 'Authorized successfully. Now return to the chat :)'


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
