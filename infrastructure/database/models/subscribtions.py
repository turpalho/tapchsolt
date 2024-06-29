from datetime import timedelta
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, BigInteger, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import User
    from .payments import Payment


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(BigInteger,
                                    primary_key=True,
                                    index=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('users.id', ondelete='CASCADE'))
    payment_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('payments.id', ondelete='CASCADE'))
    end_date = mapped_column(DateTime)

    user: Mapped["User"] = relationship(
        back_populates="subscriptions"
    )
    payment: Mapped["Payment"] = relationship(back_populates="subscription",
                                              single_parent=True)

    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (UniqueConstraint("payment_id"),)

    def __repr__(self) -> str:
        return f"Subscription: #{self.id}"