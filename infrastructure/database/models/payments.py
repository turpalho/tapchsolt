from datetime import timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import User
    from .subscribtions import Subscription


class Payment(Base):
    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.id'))
    amount: Mapped[int] = mapped_column(BigInteger)
    method: Mapped[str]

    subscription: Mapped["Subscription"]= relationship(back_populates='payment')
    user: Mapped["User"] = relationship(back_populates="payments")

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"Payment: #{self.id}"