import secrets

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse, HTMLResponse

from app.models import User
from app.utils import get_spotify

router = APIRouter()

auth_state_data = {}
authorized_response = HTMLResponse(open('app/authorized.html').read(), status_code=200)


@router.get('/')
async def authorize_spotify(request: Request, id: int, first_name: str, last_name: str, photo_url: str, username: str):
    # todo: check authorization (https://core.telegram.org/widgets/login#checking-authorization)
    state = secrets.token_urlsafe(16)
    auth_state_data[state] = dict(
        id=id,
        first_name=first_name,
        last_name=last_name,
        username=username,
        photo_url=photo_url
    )

    redirect_uri = request.url_for('spotify_callback')
    spotify = get_spotify(request.app.state.session, redirect_uri, state=state)
    return RedirectResponse(spotify.auth.get_authorize_url())


@router.get('/callback', response_class=HTMLResponse)
async def spotify_callback(request: Request, code: str, state: str):
    redirect_uri = request.url_for('spotify_callback')
    spotify = get_spotify(request.app.state.session, redirect_uri)
    token = await spotify.auth.get_token_from_code(code)
    user = await User.objects.get_or_none(id=auth_state_data[state]['id'])
    if user is None:
        await User.objects.create(
            **auth_state_data[state],
            refresh_token=token.refresh_token
        )
    auth_state_data.pop(state)
    return authorized_response
