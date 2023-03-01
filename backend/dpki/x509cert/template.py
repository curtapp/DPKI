import logging
from abc import ABC, abstractmethod
from typing import Sequence, Type, TYPE_CHECKING

from cryptography import x509
from cryptography.x509 import DNSName, RFC822Name

from names import DistinguishedName, Hierarchy

if TYPE_CHECKING:
    CommonBuilder = x509.CertificateSigningRequestBuilder | x509.CertificateBuilder
    Name = x509.Name | DistinguishedName | str


def enable_ku(*keys) -> dict:
    return dict((key, True if key in keys else False)
                for key in ('digital_signature', 'key_encipherment', 'key_cert_sign', 'crl_sign', 'key_agreement',
                            'content_commitment', 'data_encipherment', 'encipher_only', 'decipher_only'))


def get_enabled_ku(extval) -> tuple[str, ...]:
    result = []
    for key in ('digital_signature', 'key_encipherment', 'key_cert_sign', 'crl_sign',
                'key_agreement', 'content_commitment', 'data_encipherment', 'encipher_only', 'decipher_only'):
        try:
            if getattr(extval, key):
                result.append(key)
        except:
            pass
    return tuple(sorted(result))


def matches_to(builder: 'CommonBuilder') -> Type['Template'] | None:
    """ Returns matched certificate template """
    if CA.matches(builder):
        return CA
    elif Host.matches(builder):
        return Host
    elif User.matches(builder):
        return Host


class Template(ABC):
    """ Base class for x509 certificate building
    """

    @classmethod
    def apply(tmpl, builder: 'CommonBuilder', distinguished_name: 'Name', **kw) -> 'CommonBuilder':
        self = (tmpl() if issubclass(tmpl, Template) else tmpl)
        if not isinstance(distinguished_name, DistinguishedName):
            distinguished_name = DistinguishedName(distinguished_name
                                                   if isinstance(distinguished_name, str)
                                                   else distinguished_name.rfc4514_string())
        for extval, critical in self._make_extensions(distinguished_name, **kw):
            builder = builder.add_extension(extval, critical)
        return builder

    @abstractmethod
    def _make_extensions(self, distinguished_name: 'DistinguishedName', **kw):
        """ Do it """

    @classmethod
    def check_extval(tmpl, extval) -> bool:
        return True

    @classmethod
    def matches(tmpl, builder: 'CommonBuilder') -> bool:
        """ Must return true if `builder` matcher template
        """
        try:
            for extval, critical in tmpl._make_extensions(None, DistinguishedName('UID=user, DC=test')):
                ext = builder.extensions.get_extension_for_oid(extval.oid)
                if not (critical == ext.critical and tmpl.check_extval(ext.value)):
                    raise ValueError
                if isinstance(ext.value, x509.KeyUsage) and get_enabled_ku(ext.value) != get_enabled_ku(extval):
                    raise ValueError
            return True
        except Exception as exc:
            logging.exception('!!!')
            return False


class CA(Template):
    """ Certificate authority template
    """

    def _make_extensions(self, distinguished_name: DistinguishedName, path_length: int = None, **kwargs):
        return [
            (x509.BasicConstraints(ca=True, path_length=path_length), True),
            (x509.KeyUsage(**enable_ku('digital_signature', 'key_cert_sign', 'crl_sign')), True),
        ]

    @classmethod
    def check_extval(tmpl, extval) -> bool:
        if isinstance(extval, x509.BasicConstraints):
            if not extval.ca:
                return False
        return True


class Host(Template):
    """ Server (network node) template with server auth support
    """

    def _make_extensions(self, distinguished_name: DistinguishedName, san: Sequence[str] = None, **kwargs):
        san = set(san or [])
        if hierarchy := distinguished_name.extract(Hierarchy.Domain, True):
            san.add('.'.join(item[0][1] for item in hierarchy._raw))
        return [
            (x509.BasicConstraints(ca=False, path_length=None), True),
            (x509.KeyUsage(**enable_ku('digital_signature', 'key_encipherment',
                                       'key_agreement', 'content_commitment')), True),
            (x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), True),
            (x509.SubjectAlternativeName([DNSName('localhost'), *(DNSName(name) for name in san or [])]), True)
        ]


class User(Template):
    """ Шаблон для пользователя
    """

    def _make_extensions(self, distinguished_name: DistinguishedName, **kwargs):
        username = None
        if hierarchy := distinguished_name.extract(Hierarchy.Domain, False):
            if hierarchy._raw[0][0][0] == 'UID':
                username = hierarchy._raw[0][0][1]
                domain = '.'.join(item[0][1] for item in hierarchy._raw[1:])
                if domain:
                    username = '@'.join([username, domain])
        return [
            (x509.BasicConstraints(ca=False, path_length=None), True),
            (x509.KeyUsage(**enable_ku('digital_signature', 'key_encipherment',
                                       'content_commitment', 'data_encipherment')), True),
            (x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH]), True),
            *([(x509.SubjectAlternativeName([RFC822Name(username)]), True)] if username else [])
        ]
