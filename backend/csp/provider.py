from csp import ed25519, sha256
from csp.base import Hasher, EncrypterOpts, DecrypterOpts, Key, KeyOpts, HashOpts, SignerOpts


class CSProvider:
    """ Crypto service provider
    """

    def key_gen(self, opts: 'KeyOpts') -> 'Key':
        """ Generates key  with use `opts`.
        """
        if isinstance(opts, ed25519.KeyOpts):
            return ed25519.Key(ed25519.Ed25519PrivateKey.generate(), opts)
        raise NotImplementedError(f'`key_gen` with option {opts.__class__.__qualname__} not yet implemented')

    def key_derive(self, src: 'Key', opts: 'KeyOpts') -> 'Key':
        """ Derives key from `src` with use `opts`.
        """
        raise NotImplementedError(f'`key_derive` with option {opts.__class__.__qualname__} not yet implemented')

    def key_import(self, raw, opts: 'KeyOpts' = None) -> 'Key':
        """ Imports key from `raw` representation
        """
        if isinstance(opts, ed25519.KeyOpts):
            return ed25519.Key(raw, opts)
        elif isinstance(raw, ed25519.KeyTypes):
            return ed25519.Key(raw, opts)
        qn = {opts.__class__.__qualname__ if opts else raw.__class__.__qualname__}
        raise NotImplementedError(f'`key_import` from {qn} not yet implemented')

    def hash(self, msg: bytes, opts: 'HashOpts') -> bytes:
        """ Hashes message with `opts`.
        """
        if isinstance(opts, sha256.HashOpts):
            return sha256.digest(msg)
        raise NotImplementedError(f'`hash` with option {opts.__class__.__qualname__} not yet implemented')

    def get_hash(self, opts: 'HashOpts') -> 'Hasher':
        """ Returns hasher for `opts`.
        """
        if isinstance(opts, sha256.HashOpts):
            return sha256.Hasher()
        raise NotImplementedError(f'`get_hash` with option {opts.__class__.__qualname__} not yet implemented')

    def sign(self, key: 'Key', digest: bytes, opts: 'SignerOpts') -> bytes:
        """ Signs digest using `key` and `opts` """
        if isinstance(key.opts, ed25519.KeyOpts):
            raw = key.raw  # type:ed25519.Ed25519PrivateKey
            return raw.sign(self.hash(digest, opts.hash_options))
        raise NotImplementedError(f'`sign` for key {key.__class__.__qualname__} not yet implemented')

    def verify(self, pub: 'Key', signature: bytes, digest: bytes, opts: 'SignerOpts') -> bool:
        """ Verifies signature against `key` and `digest` with use `opts` """
        if isinstance(pub.opts, ed25519.KeyOpts):
            raw = pub.public_key.raw  # type:ed25519.Ed25519PublicKey
            try:
                raw.verify(signature, self.hash(digest, opts.hash_options))
                return True
            except Exception:
                return False
        raise NotImplementedError(f'`verify` for key {pub.__class__.__qualname__} not yet implemented')

    def encrypt(self, key: 'Key', plaintext: bytes, opts: 'EncrypterOpts') -> bytes:
        """ Encrypts plaintext using `key` and `opts` """
        raise NotImplementedError(f'`encrypt` with option {opts.__class__.__qualname__} not yet implemented')

    def decrypt(self, key: 'Key', ciphertext: bytes, opts: 'DecrypterOpts') -> bytes:
        """ Decrypt decrypts ciphertext using `key`  and `opts` """
        raise NotImplementedError(f'`decrypt` with option {opts.__class__.__qualname__} not yet implemented')
