from typing import TYPE_CHECKING

import tend.abci.ext
from cryptography import x509
from cryptography.x509 import CertificateSigningRequest, Certificate
from tend import abci
from tend.abci.handlers import ResponseCheckTx
from tend.abci.handlers import ResultCode

import dpki.x509cert.template
from csp.provider import CSProvider
from dpki import x509cert
from dpki.database.repository import CertEntity

if TYPE_CHECKING:
    from typing import Union, Tuple
    from . import Application

    CheckerResult = Tuple[ResultCode | int, Union[str, None, CertificateSigningRequest, Certificate]]


class CheckerMixin:
    app: 'Application'

    async def _check_tx(self, tx: bytes) -> 'CheckerResult':
        """ Checks transaction """
        if tx.startswith(b'-----BEGIN CERTIFICATE REQUEST-----'):
            csr = x509.load_pem_x509_csr(tx)
            return await self._check_csr_tx(csr)
        elif tx.startswith(b'-----BEGIN CERTIFICATE-----'):
            cert = x509.load_pem_x509_certificate(tx)
            return await self._check_cert_tx(cert)
        return ResultCode.Error, None

    async def _check_csr_tx(self, csr: 'CertificateSigningRequest') -> 'CheckerResult':
        """ Checks CSR taken from transaction """
        csp = CSProvider()
        if csr.is_signature_valid and x509cert.template.matches_to(csr):
            pub = csp.key_import(csr.public_key())
            async with self.app.database.begin() as ac:
                if pem_serialized := await CertEntity.get_by_subject(ac, csr.subject.rfc4514_string()):
                    found = x509.load_pem_x509_certificate(pem_serialized.encode('utf8'))
                    found_pub = csp.key_import(found.public_key())
                    if found_pub == pub:
                        return 100, 'Certificate already exists'
                    else:
                        return ResultCode.Error, 'Certificate for given subject already issued for an other public key'
            return ResultCode.OK, (csr if self.app.ca.cert else None)
        return ResultCode.Error, 'Wrong CSR'

    async def _check_cert_tx(self, cert: 'Certificate') -> 'CheckerResult':
        """ Checks certificate taken from transaction """
        csp = CSProvider()
        pub = csp.key_import(cert.public_key())
        if x509cert.template.matches_to(cert):
            async with self.app.database.begin() as ac:
                if pem_serialized := await CertEntity.get_by_subject(ac, cert.subject.rfc4514_string()):
                    found = x509.load_pem_x509_certificate(pem_serialized.encode('utf8'))
                    found_pub = csp.key_import(found.public_key())
                    if found_pub == pub:
                        return ResultCode.Error, 'Certificate already exists'
                    else:
                        return ResultCode.Error, 'Certificate for given subject already issued for an other public key'
                if not await CertEntity.get_by_subject(ac, cert.issuer.rfc4514_string()):
                    return ResultCode.Error, 'Certificate issuer not found'
            return ResultCode.OK, (cert if self.app.ca.cert else None)
        return ResultCode.Error, 'Wrong Certificate'


class TxChecker(abci.ext.TxChecker, CheckerMixin):
    """ TX checker
    """
    app: 'Application'

    def __init__(self, app: 'Application'):
        super(TxChecker, self).__init__(app)

    async def check_tx(self, req):
        """ ABCI method that checks transaction """
        code, payload = await self._check_tx(req.tx)
        if code == ResultCode.OK:
            return ResponseCheckTx(code=code)
        return ResponseCheckTx(code=code, log=(payload if isinstance(payload, str) else 'Unknown TX'))
