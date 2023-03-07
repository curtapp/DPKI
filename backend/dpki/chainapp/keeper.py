import json
import logging
from dataclasses import asdict
from datetime import timezone
from typing import TYPE_CHECKING

import tend.abci.ext
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.x509 import Certificate
from tend import abci
from tend.abci.handlers import ResultCode, ResponseDeliverTx

import csp.sha256
from dpki.database.repository import CertEntity, AppState
from dpki.x509cert import template
from .checker import CheckerMixin

if TYPE_CHECKING:
    from typing import Optional
    from sqlalchemy.ext.asyncio import AsyncConnection
    from . import Application

    AsyncConnection = Optional[AsyncConnection]


class TxKeeper(abci.ext.TxKeeper, CheckerMixin):
    """ TX keeper
    """
    app: 'Application'

    def __init__(self, app: 'Application'):
        self.ac = None  # type: 'AsyncConnection'
        super(TxKeeper, self).__init__(app)

    def _make_cert_entity(self, cert: 'Certificate') -> 'CertEntity':
        not_valid_before = cert.not_valid_before.replace(tzinfo=timezone.utc)
        not_valid_after = cert.not_valid_after.replace(tzinfo=timezone.utc)
        pem_serialized = cert.public_bytes(encoding=serialization.Encoding.PEM).decode('utf8')
        tmpl = template.matches_to(cert)
        if tmpl == template.CA:
            role = 'CA'
        elif tmpl:
            role = tmpl.__name__
        else:
            role = None
        return CertEntity(sn=bytes.fromhex('{0:040X}'.format(cert.serial_number)), name=cert.subject.rfc4514_string(),
                          public_key=bytes(self.app.csp.key_import(cert.public_key())), pem_serialized=pem_serialized,
                          not_valid_before=not_valid_before, not_valid_after=not_valid_after, role=role)

    async def load_genesis(self, genesis_data: bytes):
        if self.ac is None:
            self.ac = self.app.database.connect()
            await self.ac.start()
        self.app.logger.info(f'Received genesis app state with size: {len(genesis_data)}')
        cert_entities = []
        data = json.loads(genesis_data)
        hasher = self.app.csp.get_hash(csp.sha256.HashOpts())
        for pem_serialized in data['certificates']:
            cert = x509.load_pem_x509_certificate(pem_serialized.encode('utf8'), backend=default_backend())
            cert_entities.append(self._make_cert_entity(cert))
            hasher.write(pem_serialized.encode('utf8'))
        await CertEntity.insert(self.ac, cert_entities)
        return hasher.sum()

    async def begin_block(self, req):
        if self.ac is None:
            self.ac = self.app.database.connect()
            await self.ac.start()
        return await super().begin_block(req)

    async def deliver_tx(self, req):
        if self.app.logger.isEnabledFor(logging.DEBUG):
            self.app.logger.debug(f'deliver_tx: {asdict(req)}')
        code, payload = await self._check_tx(req.tx)
        if code == ResultCode.OK:
            if isinstance(payload, Certificate):
                await CertEntity.insert(self.ac, [self._make_cert_entity(payload)])
            self.app.logger.debug(f'deliver_tx: code={code}')
            return ResponseDeliverTx(code=code)
        return ResponseDeliverTx(code=code, log=(payload if isinstance(payload, str) else 'Unknown TX'))

    async def commit(self, req):
        resp = await super().commit(req)
        app_hash = resp.data
        block_height = self.block_height
        if block_height == self.app.state.block_height:
            await AppState.update(self.ac, app_hash, block_height)
        await self.ac.commit()
        await self.ac.close()
        self.ac = None
        return resp
