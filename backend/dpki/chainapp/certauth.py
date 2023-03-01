from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cryptography import x509
from sqlalchemy import select

from csp.base import Key
from .utils import normalize_config
from dpki import database as t

CertEntity = t.cert_entities.c

if TYPE_CHECKING:
    from . import Application

DEFAULT_CONFIG = dict(template=["CA", "Node", "User"],
                      ca_valid_for="795d", host_valid_for="530d", user_valid_for="365d",
                      next_path_length=3, waiting_for_downstream="900s")


class CA:
    """ Certificate authority service
    """

    def __init__(self, app: 'Application', key: Key, **config: dict):
        self.__cert = None  # type: 'x509.Certificate' | None
        self.__key = key
        self.app = app
        self.config = normalize_config({**DEFAULT_CONFIG,
                                        **dict((key, value) for key, value in config.items()
                                               if key in tuple(DEFAULT_CONFIG.keys()))})

    @property
    def ready(self):
        """ True if CA has configured and ready to work """
        return self.__cert is not None

    async def initialize(self) -> str | None:
        """ Tries to initialize. """
        async with self.app.database.begin() as ac:
            public_key = bytes(self.__key.public_key)
            select_stmt = select(t.cert_entities) \
                .where(CertEntity.not_valid_after > datetime.now(tz=timezone.utc)) \
                .where(CertEntity.public_key == public_key) \
                .where(CertEntity.revocated_at == None)
            async for obj in await ac.stream(select_stmt):
                self.__cert = x509.load_pem_x509_certificate(obj.pem_serialized.encode('utf8'))
                return self.__cert.subject.rfc4514_string()
