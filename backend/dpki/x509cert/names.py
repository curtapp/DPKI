from enum import Enum
from typing import Optional
from cryptography import x509


class Hierarchy(Enum):
    """ Distinguished name hierarchy """
    Country = tuple(['C', 'ST', 'L', 'STREET', 'CN'])
    Domain = tuple(['DC', 'UID'])
    Organization = tuple(['O', 'OU', 'CN'])
    CO = tuple(['C', 'ST', 'L', 'STREET', 'O', 'OU', 'CN'])
    OC = tuple(['O', 'C', 'ST', 'L', 'STREET', 'OU', 'CN'])


class DistinguishedName(x509.Name):
    """ Distinguished name
    """
    _raw: tuple[tuple[tuple[str, str], ...], ...]

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], str):
            super().__init__(DistinguishedName.deserialize(args[0]).rdns)
        else:
            super().__init__(*args, **kwargs)

    @property
    def raw(self) -> tuple[tuple[tuple[str, str], ...], ...]:
        """ Internal representation """
        if not self._raw:
            self._raw = self._split(self.rfc4514_string())
        return self._raw

    def select(self, hierarchy: Hierarchy) -> Optional['DistinguishedName']:
        parts = self._extract_hierarchy(hierarchy, self.raw)
        if parts:
            normalized = ','.join('='.join(b for b in a) for a in parts)
            return DistinguishedName.deserialize(normalized)

    @classmethod
    def deserialize(cls, value: str) -> 'DistinguishedName':
        """ Deserialized object from string """
        parts = cls._split(value)
        if not cls._check(parts):
            raise ValueError(f"`{value}` isn't correct distinguished name")
        normalized = ','.join('+'.join('='.join(c for c in b) for b in a) for a in parts)
        inst = cls(x509.Name.from_rfc4514_string(normalized).rdns)
        inst._raw = parts
        return inst

    def serialize(self) -> str:
        """ Serialized object to string """
        return self.rfc4514_string()

    @staticmethod
    def _extract_hierarchy(hierarchy: Hierarchy, parts: tuple[tuple[tuple[str, str]], ...]) -> tuple[tuple[str, str]]:
        result = list()
        for rdns in parts:
            for key, value in rdns:
                if key in hierarchy.value:
                    result.append((key, value))
        if len(result):
            if len(result) == 1:
                if hierarchy.value[0] in ('C', 'O') and result[0][0] == 'CN':
                    return tuple()
                elif hierarchy.value[0] == 'DC' and result[0][0] == 'UID':
                    return tuple()
            else:
                if result[-1][0] == hierarchy.value[0]:
                    if hierarchy.value[0] == 'DC' or result[0][0] == hierarchy.value[-1]:
                        return tuple(result)
                return tuple()
        return tuple(result)

    @staticmethod
    def _check(parts: tuple[tuple[tuple[str, str]], ...]) -> bool:
        if len(parts) > 1:
            c = DistinguishedName._extract_hierarchy(Hierarchy.Country, parts)
            o = DistinguishedName._extract_hierarchy(Hierarchy.Organization, parts)
            dc = DistinguishedName._extract_hierarchy(Hierarchy.Domain, parts)
            if len(c) or len(o) or len(dc):
                return True
        return False

    @staticmethod
    def _split(value: str) -> tuple[tuple[tuple[str, str], ...], ...]:
        items = list()
        for s in value.split(','):
            parts = list()
            for s in s.strip().split('+'):
                key, value = tuple(map(lambda s: s.strip(), s.strip().split('=')))
                parts.append((key.upper(), value))
            items.append(tuple(parts))
        return tuple(items)
