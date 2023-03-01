import json
from dataclasses import asdict
from datetime import timezone, datetime
from typing import TYPE_CHECKING

import tend.abci.ext
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from sqlalchemy import insert
from tend import abci

import csp.sha256
from dpki import database as t
from dpki.x509cert import template as cert_template
from ..models import CertEntity

if TYPE_CHECKING:
    from typing import Optional
    from . import Application
    from sqlalchemy.ext.asyncio import AsyncConnection


class TxKeeper(abci.ext.TxKeeper):
    """ TX keeper
    """

    app: 'Application'

    def __init__(self, *args, **kwargs):
        self.__connection = None  # type: Optional['AsyncConnection']
        super().__init__(*args, **kwargs)

    @property
    def connection(self) -> 'AsyncConnection':
        if self.__connection is None:
            raise RuntimeError('Run `begin_transaction` before use connection')
        return self.__connection

    async def begin_transaction(self):
        if self.__connection is None:
            self.__connection = self.app.database.connect()
            await self.__connection.start()

    async def end_transaction(self):
        await self.connection.commit()
        await self.connection.close()
        self.__connection = None

    async def deliver_tx(self, req):
        return await super().deliver_tx(req)

    async def load_genesis(self, genesis_data: bytes):
        await self.begin_transaction()
        self.app.logger.info(f'Received genesis app state with size: {len(genesis_data)}')
        certs = []
        data = json.loads(genesis_data)
        hasher = self.app.csp.get_hash(csp.sha256.HashOpts())
        for pem_serialized in data['certificates']:
            cert = x509.load_pem_x509_certificate(pem_serialized.encode('utf8'), backend=default_backend())
            not_valid_before = cert.not_valid_before.replace(tzinfo=timezone.utc)
            not_valid_after = cert.not_valid_after.replace(tzinfo=timezone.utc)
            role = None
            if cert_template.CA.matches(cert):
                role = 'CA'
            elif cert_template.Host.matches(cert):
                role = 'Host'
            elif cert_template.User.matches(cert):
                role = 'User'
            certs.append(asdict(
                CertEntity(sn=bytes.fromhex('{0:040X}'.format(cert.serial_number)), name=cert.subject.rfc4514_string(),
                           public_key=bytes(self.app.csp.key_import(cert.public_key())), pem_serialized=pem_serialized,
                           not_valid_before=not_valid_before, not_valid_after=not_valid_after, role=role)))
            hasher.write(pem_serialized.encode('utf8'))
        if certs:
            insert_stmt = insert(t.cert_entities)
            await self.connection.execute(insert_stmt, certs)
        return hasher.sum()

    async def begin_block(self, req):
        await self.begin_transaction()
        return await super().begin_block(req)

    async def commit(self, req):
        resp = await super().commit(req)
        app_hash = resp.data
        block_height = self.block_height
        if block_height == self.app.state.block_height:
            insert_stmt = insert(t.app_state)
            await self.connection.execute(insert_stmt, dict(app_hash=app_hash, block_height=block_height,
                                                            created_at=datetime.now(timezone.utc)))
        await self.end_transaction()
        return resp
