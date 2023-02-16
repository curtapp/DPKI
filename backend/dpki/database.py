import os
from sqlalchemy import create_engine, String, Text
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import BigInteger, DateTime, LargeBinary
from sqlalchemy import Table, Column, func
from sqlalchemy.orm import registry

mapper_registry = registry()
mapped = mapper_registry.mapped
metadata = mapper_registry.metadata

app_state = Table(
    'app_state', metadata,
    Column('created_at', DateTime(timezone=True), server_default=func.now(), primary_key=True),
    Column('block_height', BigInteger, nullable=False),
    Column('app_hash', LargeBinary, nullable=False)
)

cert_entities = Table(
    'cert_entities', metadata,
    Column('sn', LargeBinary, primary_key=True),
    Column('name', String, nullable=False, index=True),
    Column('public_key', LargeBinary, nullable=False, index=True),
    Column('pem_serialized', Text, nullable=False),
    Column('not_valid_after', DateTime, nullable=False),
    Column('not_valid_before', DateTime, nullable=False),
    Column('revocated_at', DateTime, nullable=True),
)


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
