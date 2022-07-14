from datetime import datetime

import databases
import ormar
import sqlalchemy

import config

database = databases.Database(config.DATABASE)
metadata = sqlalchemy.MetaData()


class BaseMeta(ormar.ModelMeta):
    database = database
    metadata = metadata


class User(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True, autoincrement=False)
    first_name: str = ormar.String(max_length=64)
    last_name: str | None = ormar.String(max_length=64, nullable=True)
    username: str | None = ormar.String(max_length=32, nullable=True)
    photo_url: str | None = ormar.String(max_length=256, nullable=True)
    refresh_token: str = ormar.String(max_length=256)


class TelegramGroup(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True, autoincrement=False)
    last_update: datetime = ormar.DateTime()
    title: str = ormar.String(max_length=256)
    username: str | None = ormar.String(max_length=32, nullable=True)

    users: list[User] | None = ormar.ManyToMany(User)


class Genre(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.String(max_length=256, unique=True)


class UserArtist(ormar.Model):
    class Meta(BaseMeta):
        tablename = 'users_x_artists'

    id: int = ormar.Integer(primary_key=True)
    order: int = ormar.Integer()


class Artist(ormar.Model):
    class Meta(BaseMeta):
        pass

    id: str = ormar.String(primary_key=True, max_length=256)
    name: str = ormar.String(max_length=256)
    popularity: int = ormar.Integer()
    url: str = ormar.String(max_length=256)
    image_url: str = ormar.String(max_length=256)
    followers_total: int = ormar.Integer()

    users: list[User] | None = ormar.ManyToMany(User, through=UserArtist)
    genres: list[Genre] | None = ormar.ManyToMany(Genre)
