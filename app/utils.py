import aiohttp
from spoffy import AsyncSpotify
from spoffy.io.aiohttp import make_spotify

import config
from app.models import Genre, database, Artist


def get_spotify(session: aiohttp.ClientSession, redirect_uri: str = None, state: str | None = None):
    scope = 'user-top-read'
    return make_spotify(
        session=session,
        client_id=config.SPOTIFY_API[0],
        client_secret=config.SPOTIFY_API[1],
        scope=scope,
        redirect_uri=redirect_uri,
        state=state,
    )


@database.transaction()
async def update_user(spotify: AsyncSpotify, user):
    await spotify.auth.refresh_authorization(user.refresh_token)
    first_top_page = await spotify.library.top_artists(49)
    second_top_page = await spotify.library.top_artists(50, offset=49)
    items = first_top_page.items + second_top_page.items
    for position, item in enumerate(items):
        # todo: replace the following with 'update_or_create'
        item_data = dict(
            id=item.id,
            name=item.name,
            popularity=item.popularity,
            url=item.href,
            image_url=item.images[0].url,
            followers_total=item.followers.total,
        )
        artist, created = await Artist.objects.get_or_create(id=item.id, _defaults=item_data)
        if not created:
            artist.update(**item_data)

        await artist.users.add(user, order=position)  # todo: ignore duplicates
        await artist.genres.clear()
        for genre_name in item.genres:
            genre, _ = await Genre.objects.get_or_create(name=genre_name)
            await artist.genres.add(genre)
