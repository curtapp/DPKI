from sqlalchemy import BigInteger, DateTime, LargeBinary
from sqlalchemy import String, Text
from sqlalchemy import Table, Column, func
from sqlalchemy.orm import registry

mapper_registry = registry()
mapped = mapper_registry.mapped
metadata = mapper_registry.metadata

app_state = Table(
    'app_state', metadata,
    Column('created_at', DateTime(timezone=True), server_default=func.now(), primary_key=True),
    Column('block_height', BigInteger, nullable=False),
    Column('app_hash', LargeBinary, nullable=False)
)

cert_entities = Table(
    'cert_entities', metadata,
    Column('sn', LargeBinary, primary_key=True),
    Column('name', String, nullable=False, index=True),
    Column('public_key', LargeBinary, nullable=False, index=True),
    Column('pem_serialized', Text, nullable=False),
    Column('not_valid_after', DateTime, nullable=False),
    Column('not_valid_before', DateTime, nullable=False),
    Column('revocated_at', DateTime, nullable=True),
    Column('role', String),
)
