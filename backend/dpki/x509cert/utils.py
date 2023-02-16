from datetime import date, datetime, time
from typing import TYPE_CHECKING, Type

from cryptography import x509
from cryptography.hazmat.backends import default_backend

from .names import DistinguishedName
from .template import Template


if TYPE_CHECKING:
    from csp.base import Key
    CommonBuilder = x509.CertificateSigningRequestBuilder | x509.CertificateBuilder
    IssuerPair = tuple[x509.Certificate | x509.CertificateSigningRequest, Key]


def create_csr(distinguished_name: str, key: 'Key',
               template: Template | Type[Template], **kwargs) -> x509.CertificateSigningRequest:
    """ Creates certificate signing request (CSR) """
    subject_name = DistinguishedName(distinguished_name)
    builder = x509.CertificateSigningRequestBuilder().subject_name(subject_name)
    builder = template.apply(builder, subject_name, **kwargs)
    return builder.sign(private_key=key.raw, algorithm=None, backend=default_backend())


def apply_csr(csr: x509.CertificateSigningRequest, issuer_pair: 'IssuerPair',
              not_valid_after: date | str, not_valid_before: date | str = None) -> x509.Certificate:
    """ Create and sings certificate based on CSR """

    def normalize_if_str(value):
        return date.fromisoformat(value) if isinstance(value, str) else value

    issuer, key = issuer_pair
    not_valid_after = datetime.combine(normalize_if_str(not_valid_after), time(23, 59, 59))
    not_valid_before = datetime.combine(normalize_if_str(not_valid_before) or date.today(), time(0, 0, 0))
    builder = x509.CertificateBuilder(subject_name=csr.subject,
                                      extensions=list(csr.extensions),
                                      public_key=csr.public_key()) \
        .issuer_name(issuer.subject) \
        .not_valid_before(not_valid_before).not_valid_after(not_valid_after) \
        .serial_number(x509.random_serial_number())
    return builder.sign(private_key=key.raw, algorithm=None, backend=default_backend())
