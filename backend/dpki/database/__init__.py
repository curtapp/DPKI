import os
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine


def get_database_url(sync=False):
    database_url = os.environ.get('DATABASE_URL', 'sqlite+aiosqlite:///.data/database.db')
    if sync:
        for async_item in ['+asyncpg', '+aiosqlite']:
            if async_item in database_url:
                database_url = database_url.replace(async_item, '')
                break
        else:
            raise ValueError(f"Cannot get sync url from {database_url}")
        return database_url
    else:
        return database_url


def engine_factory(sync=False):
    if sync:
        return create_engine(get_database_url(sync=True))
    else:
        return create_async_engine(get_database_url(sync=False))

