import asyncio
import os.path
from datetime import date, timedelta
from typing import TYPE_CHECKING

from cryptography import x509
from cryptography.hazmat.primitives import serialization

from dpki.database.repository import CertEntity
from dpki.x509cert import apply_csr
from dpki.x509cert import template
from dpki.utils import load_from_key_file, normalize_config, load_config

from .client import ClientRPC
from .utils import can_issue_csr

if TYPE_CHECKING:
    from logging import Logger
    from typing import Optional
    from cryptography.x509 import Certificate, CertificateSigningRequest
    from sqlalchemy.ext.asyncio import AsyncEngine


class CA:
    """ Certificate authority
    """
    DEFAULT_CONFIG = dict(allow_templates=["CA", "Node", "User"], next_path_length=3,
                          ca_valid_for="795d", host_valid_for="530d", user_valid_for="365d",
                          waiting_for_downstream="300s")

    def __init__(self, database: 'AsyncEngine', home_path: str, logger: 'Logger' = None):
        self.database = database
        self.logger = logger
        config = load_config(home_path)
        self.client_rpc = ClientRPC(config.get('rpc', {}).get('laddr', 'tcp://127.0.0.1:26657'))
        self.__key = (load_from_key_file(os.path.join(home_path, config['ca']['ca_key_file']))
                      if 'ca' in config else None)
        self.config = normalize_config({**CA.DEFAULT_CONFIG,
                                        **dict((key, value) for key, value in config.get('ca', {}).items()
                                               if key in tuple(CA.DEFAULT_CONFIG.keys()))})
        self.__chain = []

    @property
    def cert(self) -> 'Optional[Certificate]':
        """ CA cert if present """
        return self.__chain[0] if self.__key else None

    @property
    def root(self) -> 'Certificate':
        """ CA root cert """
        return self.__chain[-1]

    async def initialize(self) -> str | None:
        """ Tries to initialize. """
        result = None
        async with self.database.begin() as ac:
            public_key = bytes(self.__key.public_key)
            pem_serialized = await CertEntity.get_by_public_key(ac, public_key)
            if pem_serialized:  # if CA cert present
                cert = x509.load_pem_x509_certificate(pem_serialized.encode('utf8'))
                result = cert.subject.rfc4514_string()
                self.__chain.append(cert)
                while cert.subject.public_bytes() != cert.issuer.public_bytes():  # load CA certificate chain
                    pem_serialized = await CertEntity.get_by_subject(ac, cert.issuer.rfc4514_string())
                    if pem_serialized:
                        cert = x509.load_pem_x509_certificate(pem_serialized.encode('utf8'))
                        self.__chain.append(cert)
            else:
                pem_serialized = await CertEntity.list_by_role(ac, 'CA Root', 1)
                if pem_serialized:
                    self.__chain.append(x509.load_pem_x509_certificate(pem_serialized[0].encode('utf8')))
                else:
                    raise RuntimeError('Not found active CA root cert')
        return result

    def in_namespace(self, csr: 'CertificateSigningRequest') -> 'bool':
        """ Returns true if subject in pki namespace """
        return can_issue_csr(self.root, csr) > 0

    async def issue_iiiy(self, csr: 'CertificateSigningRequest'):
        distance = can_issue_csr(self.cert, csr)
        if distance < 1:
            return
        asyncio.create_task(self._issue_csr(csr, (distance - 1) * self.config['waiting_for_downstream']))

    async def _issue_csr(self, csr: 'CertificateSigningRequest', pre_timeout: int):
        await asyncio.sleep(pre_timeout)
        tmpl = template.matches_to(csr)
        if tmpl == template.CA:
            valid_for = self.config['ca_valid_for']
        elif tmpl == template.Host:
            valid_for = self.config['host_valid_for']
        elif tmpl == template.User:
            valid_for = self.config['host_valid_for']
        else:
            raise RuntimeError('Unexpected template')
        not_valid_after = date.today() + timedelta(days=valid_for)
        cert = apply_csr(csr, (self.cert, self.__key), not_valid_after=not_valid_after)
        await self.client_rpc.send_tx(cert.public_bytes(encoding=serialization.Encoding.PEM))
