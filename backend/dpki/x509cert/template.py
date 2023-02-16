from abc import ABC, abstractmethod
from typing import Sequence

from cryptography import x509
from cryptography.x509 import DNSName, RFC822Name

from dpki.x509cert.names import DistinguishedName, Hierarchy

CommonBuilder = x509.CertificateSigningRequestBuilder | x509.CertificateBuilder
DN = x509.Name | DistinguishedName | str


def enable_ku(*keys) -> dict:
    return dict((key, True if key in keys else False)
                for key in ('digital_signature', 'key_encipherment', 'key_cert_sign', 'crl_sign', 'key_agreement',
                            'content_commitment', 'data_encipherment', 'encipher_only', 'decipher_only'))


class Template(ABC):
    """ Base class for x509 certificate building
    """

    @classmethod
    def apply(tmpl, builder: 'CommonBuilder', distinguished_name: 'DN', **kw) -> 'CommonBuilder':
        self = (tmpl() if issubclass(tmpl, Template) else tmpl)
        if isinstance(distinguished_name, str):
            distinguished_name = DistinguishedName.deserialize(distinguished_name)
        elif isinstance(distinguished_name, x509.Name):
            distinguished_name = DistinguishedName.deserialize(distinguished_name.rfc4514_string())
        for extval, critical in self._make_extensions(distinguished_name, **kw):
            builder = builder.add_extension(extval, critical)
        return builder

    @abstractmethod
    def _make_extensions(self, distinguished_name: DistinguishedName, **kw):
        """ Do it """


class CA(Template):
    """ Certificate authority template
    """

    def _make_extensions(self, distinguished_name: DistinguishedName, path_length: int = None, **kwargs):
        return [
            (x509.BasicConstraints(ca=True, path_length=path_length), True),
            (x509.KeyUsage(**enable_ku('digital_signature', 'key_cert_sign', 'crl_sign')), True),
        ]


class Node(Template):
    """ Server (network node) template with server auth support
    """

    def _make_extensions(self, distinguished_name: DistinguishedName, san: Sequence[str] = None, **kwargs):
        san = list(san or [])
        if hierarchy := distinguished_name.select(Hierarchy.Domain):
            san.append('.'.join([value for key, value in [item[0] for item in hierarchy.raw] if key == 'DC']))
        return [
            (x509.BasicConstraints(ca=False, path_length=None), True),
            (x509.KeyUsage(**enable_ku('digital_signature', 'key_encipherment',
                                       'key_agreement', 'content_commitment')), True),
            (x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), True),
            (x509.SubjectAlternativeName([DNSName('localhost'), *([DNSName(name)] for name in san or [])]), True)
        ]


class User(Template):
    """ Шаблон для пользователя
    """

    def _make_extensions(self, distinguished_name: DistinguishedName, **kwargs):
        username = None
        if hierarchy := distinguished_name.select(Hierarchy.Domain):
            domain = '.'.join([value for key, value in [item[0] for item in hierarchy.raw] if key == 'DC'])
            uid = dict(distinguished_name.raw[0]).get('UID')
            if uid:
                username = '@'.join([uid, domain])
        return [
            (x509.BasicConstraints(ca=False, path_length=None), True),
            (x509.KeyUsage(**enable_ku('digital_signature', 'key_encipherment',
                                       'content_commitment', 'data_encipherment')), True),
            (x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]), True),
            *([(x509.SubjectAlternativeName([RFC822Name(username)]), True)] if username else [])
        ]
