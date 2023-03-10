import asyncio
import os.path
from datetime import date, timedelta
from typing import TYPE_CHECKING

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from dpki.database.repository import CertEntity
from dpki.utils import load_from_key_file, normalize_config, load_config, Service
from dpki.x509cert import apply_csr
from dpki.x509cert import template
from names import DistinguishedName, Hierarchy

if TYPE_CHECKING:
    from logging import Logger
    from typing import Optional
    from cryptography.x509 import Certificate, CertificateSigningRequest
    from sqlalchemy.ext.asyncio import AsyncEngine


class ClientRPC:
    """ HTTP client to calling chain RPC
    """

    def __init__(self, laddr):
        self.base_url = f'http://{laddr.split("//")[1]}'

    async def send_tx(self, tx: bytes):
        r = httpx.post('http://localhost:26657/broadcast_tx_async', data=dict(tx='0x' + tx.hex()))
        if r.is_error:
            raise RuntimeError('Cannot send TX')


class CA(Service):
    """ Certificate authority service
    """
    DEFAULT_CONFIG = dict(allow_templates=["CA", "Node", "User"], next_path_length=3,
                          ca_valid_for="795d", host_valid_for="530d", user_valid_for="365d",
                          waiting_for_downstream="300s")

    def __init__(self, database: 'AsyncEngine', home_path: str, logger: 'Logger' = None):
        super(CA, self).__init__(logger)
        self.database = database
        config = load_config(home_path)
        self.client_rpc = ClientRPC(config.get('rpc', {}).get('laddr', 'tcp://127.0.0.1:26657'))
        self.config = normalize_config({**CA.DEFAULT_CONFIG,
                                        **dict((key, value) for key, value in config.get('ca', {}).items()
                                               if key in tuple(CA.DEFAULT_CONFIG.keys()))})
        self.__chain = []
        self.__key = (load_from_key_file(os.path.join(home_path, config['ca']['ca_key_file']))
                      if 'ca' in config else None)

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
                result = await CertEntity.list_by_role(ac, 'CA Root', 1)
                if result:
                    self.__chain.append(x509.load_pem_x509_certificate(result[0].pem_serialized.encode('utf8')))
                else:
                    raise RuntimeError('Not found active CA root cert')
        return result

    def can_issue_csr(self, csr: 'CertificateSigningRequest') -> int:
        """ Returns true if subject in pki namespace """
        if self.cert:
            cert_dn = DistinguishedName(self.cert.subject.rfc4514_string())
            csr_dn = DistinguishedName(csr.subject.rfc4514_string())
            return max(
                cert_dn.distance(Hierarchy.Country, csr_dn),
                cert_dn.distance(Hierarchy.Organization, csr_dn),
                cert_dn.distance(Hierarchy.Domain, csr_dn),
            )
        return 0

    async def issue_iiiy(self, csr: 'CertificateSigningRequest'):
        distance = self.can_issue_csr(csr)
        if distance < 1:
            return
        self.create_task(self._issue_csr(csr, (distance - 1) * self.config['waiting_for_downstream']))

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
