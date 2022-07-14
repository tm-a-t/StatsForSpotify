from datetime import timedelta, datetime

from fastapi import FastAPI
from telethon import TelegramClient, events, Button
from telethon.tl import types as tl_types
from telethon.tl.custom import Message

import config
from app.models import database, TelegramGroup, Artist, User
from app.utils import get_spotify, update_user


class BotClient(TelegramClient):
    me: tl_types.User
    app: FastAPI

    async def run(self):
        self.add_event_handler(self.on_new_message, events.NewMessage())

        await self.connect()
        self.me = await self.sign_in(bot_token=config.BOT_TOKEN)

    async def on_new_message(self, message: Message):
        if not message.is_group:
            await message.respond(
                'Add me to some group plz',
                buttons=Button.url('Add to chat', f't.me/{self.me.username}?startgroup=true')
            )
            return
        text = message.text.removesuffix('@' + self.me.username)
        if text == '/top':
            await self.send_stats(message.chat)
            return

    async def send_stats(self, chat: tl_types.Chat | tl_types.Channel):
        message = await self.send_message(chat.id, 'Loading...')

        chat_data = dict(title=chat.title, username=chat.username)
        chat_model, created = await TelegramGroup.objects.get_or_create(
            id=chat.id,
            _defaults=dict(last_update=datetime.min, **chat_data)
        )
        if not created:
            await chat_model.update(**chat_data)

        if chat_model.last_update is None or datetime.now() - chat_model.last_update > timedelta(hours=1):
            await self.update_chat(chat_model)

        artists = await Artist.objects.all()  # todo: get relevant artists
        artists_text = '\n'.join(f'{i}. {artist.name}' for i, artist in enumerate(artists[:15], start=1))
        artists_text = artists_text or 'No data'

        users = await User.objects.all()  # todo: get relevant users
        users_text = ', '.join(f'{user.first_name} {user.last_name or ""}'.strip() for user in users)
        users_text = users_text or 'No data'

        text = (
            f'Top artists:\n'
            f'{artists_text}\n'
            f'\n'
            f'Stats based on data from: {users_text}'
        )
        auth_button = Button.auth('Authorize', config.DOMAIN)
        await message.edit(text, buttons=auth_button)

    async def update_chat(self, chat_model):
        await self.update_chat_users(chat_model)
        for user in chat_model.users:
            spotify = get_spotify(self.app.state.session)
            await update_user(spotify, user)
        await chat_model.update(last_update=datetime.now())

    @database.transaction()
    async def update_chat_users(self, chat_model):
        await chat_model.users.clear()
        async for member in self.iter_participants(chat_model.id):
            user = await User.objects.get_or_none(id=member.id)
            if user is not None:
                await chat_model.users.add(user)
