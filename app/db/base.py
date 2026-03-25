from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.db.models.outbox import Outbox  # noqa: E402, F401
from app.db.models.payment import Payment  # noqa: E402, F401