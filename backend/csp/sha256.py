import hashlib
from dataclasses import dataclass

from csp import base


@dataclass
class HashOpts(base.HashOpts):
    algorithm: str = 'sha256'


class Hasher(base.Hasher):
    """ sha256 hasher"""

    def __init__(self):
        self.__raw = hashlib.sha256()

    @property
    def size(self) -> int:
        return self.__raw.digest_size

    @property
    def block_size(self) -> int:
        return self.__raw.block_size

    def write(self, block: bytes) -> int:
        self.__raw.update(block)
        return len(block)

    def sum(self, prefix: bytes = None) -> bytes:
        return (prefix or b'') + self.__raw.digest()


def digest(block: bytes, prefix: bytes = None) -> bytes:
    hasher = Hasher()
    hasher.write(block)
    return hasher.sum(prefix)
