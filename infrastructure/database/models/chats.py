from datetime import timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import User


class Chat(Base):
    __tablename__ = "chats"

    chat_id: Mapped[int] = mapped_column(BigInteger,
                                         primary_key=True,
                                         index=True)
    name: Mapped[Optional[str]]
    url: Mapped[Optional[str]]
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey("users.id", ondelete='CASCADE'))

    user: Mapped[list["User"]] = relationship(back_populates="chats")

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"Chat: #{self.name}"
