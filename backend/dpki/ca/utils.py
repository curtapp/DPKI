from typing import TYPE_CHECKING, Protocol, runtime_checkable

from cryptography import x509
from names import dn as base
from names import Hierarchy


@runtime_checkable
class HasSubject(Protocol):
    subject: x509.Name


if TYPE_CHECKING:
    from cryptography.x509 import Certificate, CertificateSigningRequest

    DistinguishedSource = Certificate | CertificateSigningRequest | HasSubject | tuple | str


class DistinguishedName(base.DistinguishedName):
    """ Distinguished name
    """

    def __init__(self, src: 'DistinguishedSource'):
        if isinstance(src, HasSubject):
            src = src.subject.rfc4514_string()
        super().__init__(src)


def can_issue_csr(cert: 'Certificate', csr: 'CertificateSigningRequest') -> int:
    """ Returns not 0 if certificate can issue for a given csr. Positive result is distance from cert to csr. """
    cert_dn = DistinguishedName(cert)
    csr_dn = DistinguishedName(csr)
    return max(
        cert_dn.distance(Hierarchy.Country, csr_dn),
        cert_dn.distance(Hierarchy.Organization, csr_dn),
        cert_dn.distance(Hierarchy.Domain, csr_dn),
    )
