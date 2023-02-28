"""
Distinguished name class and utilities
"""
from enum import Enum
from typing import Optional


class Hierarchy(Enum):
    """ Distinguished name hierarchy """
    Country = tuple(['C', 'ST', 'L', 'STREET', 'CN'])
    Domain = tuple(['DC', 'UID'])
    Organization = tuple(['O', 'OU', 'CN'])


class DistinguishedName:
    """ Distinguished name
    """

    def __init__(self, src: str | bytes | tuple[tuple[tuple[str, str], ...], ...] | tuple[tuple[str, str], ...]):
        try:
            if isinstance(src, tuple) and isinstance(src[0], tuple):
                if isinstance(src[0][0], tuple) and isinstance(src[0][0][0], str):
                    self._raw = src
                elif isinstance(src[0][0], str):
                    self._raw = tuple(tuple(((k, v),) for k, v in item) for item in src)
            elif isinstance(src, (str, bytes)):
                src = src.decode('utf8') if isinstance(src, bytes) else src
                items = list()
                for s in src.split(','):
                    parts = list()
                    for s in s.strip().split('+'):
                        key, value = tuple(map(lambda s: s.strip(), s.strip().split('=')))
                        parts.append((key.upper(), value))
                    items.append(tuple(parts))
                self._raw = tuple(items)
            else:
                raise ValueError
        except Exception:
            raise ValueError('Wrong constructor parameters')

    def __str__(self):
        return ','.join('+'.join('='.join(part) for part in item) for item in self._raw)

    def __bytes__(self):
        return str(self).encode('utf8')

    def __eq__(self, other: 'DistinguishedName'):
        return self._raw == other._raw

    def extract(self, hierarchy: Hierarchy, base: bool = False) -> Optional['DistinguishedName']:
        """ Extracts a given hierarchy DN """
        result = tuple(tuple((key, value) for key, value in item if key in hierarchy.value) for item in self._raw)
        result = result[1:] if base and result[0][0][0] == hierarchy.value[-1] else result
        result = tuple(filter(lambda a: a, result))
        if result and result[-1][0][0] == hierarchy.value[0]:
            return DistinguishedName(result)
