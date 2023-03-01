from typing import TYPE_CHECKING
from cryptography import x509

if TYPE_CHECKING:
    from cryptography.x509 import Certificate, CertificateSigningRequest


def can_issue(issuer: 'Certificate', csr: 'CertificateSigningRequest') -> bool:
    """ Returns true if a given issuer certificate can issue a given signing request """
