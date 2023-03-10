import asyncio
import json

import tend.abci.ext
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from tend import abci
from tend.abci.handlers import RequestQuery, ResponseQuery, ResultCode

from csp.provider import CSProvider
from dpki import database
from dpki.database.repository import AppState, CertEntity

from .checker import TxChecker
from .keeper import TxKeeper
from ..caservice import CA


class Application(abci.ext.Application):
    """ ABCI Chain application
    """

    def __init__(self, home_path: str, logger=None):
        super().__init__(TxChecker(self), TxKeeper(self), logger)
        self.csp = CSProvider()
        self.database = database.engine_factory()
        self.ca = CA(self.database, home_path, logger)

    async def get_initial_app_state(self):
        self._ca = asyncio.create_task(self.ca.start())
        async with self.database.begin() as ac:
            return await AppState.get_initial(ac)

    async def update_app_state(self, new_state: 'AppState'):
        await super().update_app_state(new_state)
        if new_state.block_height > 1:
            ca_subject = await self.ca.initialize()
            if ca_subject:
                self.logger.info(f"CA initialized on this node; subject: {ca_subject}")

    async def query(self, req: 'RequestQuery') -> 'ResponseQuery':
        result = list()
        if req.path.lower() == 'ca/list':
            async with self.database.begin() as ac:
                ca_list = await CertEntity.list_by_role(ac, 'CA')
                for ca in ca_list:
                    cert = x509.load_pem_x509_certificate(ca.pem_serialized.encode('utf8'), backend=default_backend())
                    path_length = cert.extensions.get_extension_for_class(x509.BasicConstraints).value.path_length
                    result.append(dict(subject=ca.subject_name,path_length=path_length,
                                       issuer=cert.issuer.rfc4514_string()))
                return ResponseQuery(code=ResultCode.OK, height=self.state.block_height,
                                     value=json.dumps(result, ensure_ascii=False).encode('utf8'))
        return await super().query(req)
