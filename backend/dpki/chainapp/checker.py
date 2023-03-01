from typing import TYPE_CHECKING
import tend.abci.ext
from cryptography import x509
from tend import abci
from tend.abci.handlers import ResultCode, ResponseCheckTx

if TYPE_CHECKING:
    from typing import Optional, Tuple
    from . import Application
    from cryptography.x509 import CertificateSigningRequest

    Result = Tuple[ResultCode, Optional[str]]


class TxChecker(abci.ext.TxChecker):
    """ TX checker
    """
    app: 'Application'

    async def check_tx(self, req):
        code, log = await TxChecker.run(self.app, req.tx)
        return ResponseCheckTx(code=code, log=log)

    @staticmethod
    async def run(app: 'Application', tx: bytes) -> 'Result':
        if tx.startswith(b'-----BEGIN CERTIFICATE REQUEST-----'):
            csr = x509.load_pem_x509_csr(tx)
            return TxChecker.check_csr(app, csr)
        return ResultCode.Error, 'Unrecognized tx'

    @staticmethod
    def check_csr(app: 'Application', csr: 'CertificateSigningRequest') -> 'Result':
        if csr.is_signature_valid:
            return ResultCode.OK, None
        return ResultCode.Error, 'Wrong CSR'
