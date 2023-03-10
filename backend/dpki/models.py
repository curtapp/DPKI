from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True)
class CertEntity:
    """ Records for certificates and their status

    Attributes:
        sn: Serial number.
        name: Distinguished name.
        public_key: Bytes representation of public key.
        pem_serialized: PEM serialized certificate.
        not_valid_before: Certificate valid from this date.
        not_valid_after: Certificate valid till this date.
        revocated_at: Certificate has revocated from this date.
        function: Describes certificates' function
    """
    sn: bytes
    name: str
    public_key: bytes
    pem_serialized: str
    not_valid_after: datetime
    not_valid_before: datetime
    revocated_at: datetime = None
    function: str = None
