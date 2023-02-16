from abc import ABC, abstractmethod

from .opts import HashOpts


class Hasher(ABC):
    """ Hasher interface
    """

    def __init__(self, opts: HashOpts):
        self.__opts = opts

    @property
    def opts(self) -> HashOpts:
        """ Options used during creation
        """
        return self.__opts

    @property
    @abstractmethod
    def size(self) -> int:
        """ Hash size in bytes
        """

    @property
    @abstractmethod
    def block_size(self) -> int:
        """ Max data block size
        """

    @abstractmethod
    def write(self, block: bytes) -> int:
        """ Sends data block to hash.
        """

    @abstractmethod
    def sum(self, prefix: bytes = None) -> bytes:
        """ Returns current hash with prefix if present. It does not reset hasher.
        """


class BlockHasher(Hasher):
    """ Block hasher interface
    """

    def write(self, block: bytes) -> int:
        raise RuntimeError('Not applicable for a block hasher')

    @abstractmethod
    def write_data(self, block: bytes) -> bytes:
        """ Sends tx data to hash to build block hash.

        Returns:
            Digest (Hash of TX)
        """

    @abstractmethod
    def write_hash(self, block: bytes):
        """ Sends ready tx data hash to build block hash.
        """

    @abstractmethod
    def sum(self, prefix: bytes = None) -> bytes:
        """ Returns current block hash with prefix if present.  It does not reset hasher.
        """
