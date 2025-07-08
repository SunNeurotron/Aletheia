# aletheia_common/db/custom_types.py
import uuid as uuid_pkg
from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as string.
    """
    impl = String(32) # Default implementation for non-PG dialects
    cache_ok = True

    def __init__(self, as_uuid=True, *args, **kwargs):
        self.as_uuid = as_uuid
        super(UUID, self).__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(String(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name != 'postgresql':
            if isinstance(value, uuid_pkg.UUID):
                return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            if self.as_uuid and isinstance(value, str): return uuid_pkg.UUID(value)
            return value
        else:
            if self.as_uuid:
                if isinstance(value, uuid_pkg.UUID): return value
                try:
                    return uuid_pkg.UUID(value)
                except (TypeError, ValueError):
                    return value
            return value
