from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select, insert, desc

from dpki.database import models
from dpki.database.tables import app_state, cert_entities

if TYPE_CHECKING:
    from typing import Sequence
    from sqlalchemy.ext.asyncio import AsyncConnection

    CertEntities = Sequence['CertEntity']


class Repo(type):
    def __new__(mcls, name, model, attr, *, table):
        attr['c'] = table.c
        attr['t'] = table
        return type.__new__(mcls, name, model, attr)


@dataclass(kw_only=True)
class AppState(models.AppState, metaclass=Repo, table=app_state):
    """ AppState with repository methods
    """

    @staticmethod
    async def get_initial(ac: 'AsyncConnection') -> 'AppState':
        select_stmt = select(AppState.c['app_hash', 'block_height']).order_by(desc(AppState.c.created_at)).limit(1)
        async for obj in await ac.stream(select_stmt):
            return AppState(**obj._asdict())
        return AppState()

    @staticmethod
    async def update(ac: 'AsyncConnection', app_hash, block_height):
        await ac.execute(insert(AppState.t),
                         dict(app_hash=app_hash, block_height=block_height, created_at=datetime.now(timezone.utc)))


@dataclass(kw_only=True)
class CertEntity(models.CertEntity, metaclass=Repo, table=cert_entities):
    """ CertEntity with repository methods
    """

    @staticmethod
    async def insert(ac: 'AsyncConnection', items: 'CertEntities'):
        if items:
            insert_stmt = insert(CertEntity.t)
            await ac.execute(insert_stmt, [asdict(item) for item in items])

    @staticmethod
    async def get_by_public_key(ac: 'AsyncConnection', public_key: bytes) -> str | None:
        """ Return serialized certificate by public_key """
        select_stmt = select(CertEntity.c) \
            .where(CertEntity.c.not_valid_after > datetime.now(tz=timezone.utc)) \
            .where(CertEntity.c.public_key == public_key) \
            .where(CertEntity.c.revocated_at == None)
        async for obj in await ac.stream(select_stmt):
            return obj.pem_serialized

    @staticmethod
    async def get_by_subject(ac: 'AsyncConnection', subject_name: str) -> str | None:
        """ Return serialized certificate by subject name """
        select_stmt = select(CertEntity.c) \
            .where(CertEntity.c.not_valid_after > datetime.now(tz=timezone.utc)) \
            .where(CertEntity.c.subject_name == subject_name) \
            .where(CertEntity.c.revocated_at == None)
        async for obj in await ac.stream(select_stmt):
            return obj.pem_serialized

    @staticmethod
    async def list_by_role(ac: 'AsyncConnection', role: str, limit=500, offset=0) -> list['CertEntity']:
        """ Return list of serialized certificates with requested role """
        result = []
        select_stmt = select(CertEntity.c) \
            .where(CertEntity.c.not_valid_after > datetime.now(tz=timezone.utc)) \
            .where(CertEntity.c.role == role) \
            .where(CertEntity.c.revocated_at == None).limit(limit).offset(offset)
        async for obj in await ac.stream(select_stmt):
            result.append(CertEntity(**obj._asdict()))
        return result
