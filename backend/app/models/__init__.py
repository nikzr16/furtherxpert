"""Import every model so `Base.metadata` (and Alembic autogenerate) sees them."""

from app.models.user import User  # noqa: F401
