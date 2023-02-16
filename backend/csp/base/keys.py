from abc import ABC, abstractmethod

from .opts import KeyOpts


class Key(ABC):
    """ Key interface
    """

    @property
    @abstractmethod
    def raw(self):
        """ Raw representation of key
        """

    @property
    @abstractmethod
    def opts(self) -> KeyOpts:
        """ Options used during creation
        """

    @abstractmethod
    def __bytes__(self) -> bytes:
        """ Bytes representation """

    @property
    @abstractmethod
    def symmetric(self) -> bool:
        """ True if key is symmetric
        """

    @property
    @abstractmethod
    def private(self) -> bool:
        """ True if key is private
        """

    @property
    @abstractmethod
    def public_key(self) -> 'Key':
        """ Returns public key
        """
