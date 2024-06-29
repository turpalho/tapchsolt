from datetime import timedelta
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, BigInteger, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .languages import Language
    from .users import User


class Translation(Base):
    __tablename__ = 'translations'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    text: Mapped[str]
    language_code: Mapped[str] = mapped_column(String(10),
                                               ForeignKey("languages.code",
                                                          ondelete='CASCADE'))
    user_id: Mapped[int] = mapped_column(BigInteger,
                                         ForeignKey('users.id',
                                                    ondelete="CASCADE"))

    language: Mapped["Language"] = relationship(back_populates="translations")
    user: Mapped["User"] = relationship(back_populates="translations")

    __mapper_args__ = {"eager_defaults": True}

    def __repr__(self) -> str:
        return f"Translation: #{self.text}"

    @classmethod
    async def get_random_translates(cls, language_code: str):
        with cls.db_session as session:
            stmt = (select(cls)
                    .where(cls.language_code == language_code)
                    .order_by(func.random())
                    .limit(3)
                )
            result = await session.execute(stmt)
        return result.scalars().all()