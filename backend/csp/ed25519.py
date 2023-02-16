from dataclasses import dataclass

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from csp import base

KeyTypes = (Ed25519PrivateKey, Ed25519PublicKey)


@dataclass(kw_only=True)
class KeyOpts(base.KeyOpts):
    private: bool = True
    ephemeral: bool = False
    algorithm: str = 'ed25519'


class Key(base.Key):
    """ Implementation of `csp.base.Key` for ed25519 keys
    """

    def __init__(self, raw: bytes | Ed25519PrivateKey | Ed25519PublicKey = None, opts: KeyOpts = None):
        if raw is not None:
            if isinstance(raw, bytes):
                assert opts, "`opts` must be defined if first parameters is bytes"
                if opts.private:
                    self.__raw = Ed25519PrivateKey.from_private_bytes(raw[:32])
                else:
                    self.__raw = Ed25519PublicKey.from_public_bytes(raw)
            else:
                self.__raw = raw
                opts = KeyOpts(private=isinstance(raw, Ed25519PrivateKey))
        else:
            self.__raw = Ed25519PrivateKey.generate()
            opts = KeyOpts(private=True)
        self.__opts = opts

    def __bytes__(self) -> bytes:
        return (self.raw.private_bytes(encoding=serialization.Encoding.Raw,
                                       format=serialization.PrivateFormat.Raw,
                                       encryption_algorithm=serialization.NoEncryption())
                if self.private else self.raw.public_bytes(encoding=serialization.Encoding.Raw,
                                                           format=serialization.PublicFormat.Raw))

    @property
    def public_key(self) -> 'Key':
        return Key(self.__raw.public_key(), KeyOpts(private=False)) if self.private else self

    @property
    def raw(self) -> Ed25519PrivateKey | Ed25519PublicKey:
        return self.__raw

    @property
    def opts(self) -> KeyOpts:
        return self.__opts

    @property
    def private(self) -> bool:
        return self.__opts.private

    @property
    def symmetric(self) -> bool:
        return False
