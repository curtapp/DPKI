from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cryptography import x509
from sqlalchemy import select
from dpki import database as t

CertEntity = t.cert_entities.c

if TYPE_CHECKING:
    from cryptography.x509 import Certificate
    from sqlalchemy.ext.asyncio import AsyncEngine
    from csp.base import Key

from .config import DEFAULT as DEFAULT_CONFIG


class CA:
    """ Certificate authority
    """
    DEFAULT_CONFIG = DEFAULT_CONFIG

    def __init__(self, database: 'AsyncEngine', key: 'Key', **config):
        self.database = database
        self.config = config
        self.__cert = None
        self.__key = key

    @property
    def cert(self) -> 'Certificate':
        return self.__cert

    @property
    def ready(self) -> bool:
        """ True if CA has configured and ready to work """
        return self.__cert is not None

    async def initialize(self) -> str | None:
        """ Tries to initialize. """
        async with self.database.begin() as ac:
            public_key = bytes(self.__key.public_key)
            select_stmt = select(t.cert_entities) \
                .where(CertEntity.not_valid_after > datetime.now(tz=timezone.utc)) \
                .where(CertEntity.public_key == public_key) \
                .where(CertEntity.revocated_at == None)
            async for obj in await ac.stream(select_stmt):
                self.__cert = x509.load_pem_x509_certificate(obj.pem_serialized.encode('utf8'))
                return self.__cert.subject.rfc4514_string()
