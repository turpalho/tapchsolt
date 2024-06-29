from datetime import timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import User
    from .translations import Translation


class Language(Base):
    __tablename__ = 'languages'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(10), index=True, unique=True)
    title: Mapped[Optional[str]]

    users: Mapped[list["User"]] = relationship(back_populates="language")
    translations: Mapped[list["Translation"]] = relationship(back_populates="language")

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"Language: #{self.code}"