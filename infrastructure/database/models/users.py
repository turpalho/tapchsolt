from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, ForeignKey, String, update
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from .base import Base

if TYPE_CHECKING:
    from .chats import Chat
    from .payments import Payment
    from .subscribtions import Subscription
    from .languages import Language
    from .translations import Translation


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)  # tg_user_id
    user_id: Mapped[int] = synonym("id")

    username: Mapped[Optional[str]]
    tg_first_name: Mapped[Optional[str]]
    tg_last_name: Mapped[Optional[str]]
    tg_username: Mapped[Optional[str]]

    language_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("languages.code", ondelete='CASCADE'),
        nullable=False)

    language: Mapped["Language"] = relationship(back_populates="users")
    translations: Mapped[list["Translation"]] = relationship(back_populates='user')
    payments: Mapped[list["Payment"]] = relationship(back_populates='user')
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates='user')
    chats: Mapped[list["Chat"]] = relationship(back_populates="user",
                                               secondary='userchat')

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    async def update_user(cls, user_id: int, **kwargs):
        with cls.db_session as session:
            stmt = update(cls).where(cls.id == user_id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()

    @classmethod
    async def update_user_language(cls, user_id: int, lang_code: str):
        with cls.db_session as session:
            stmt = update(cls).where(cls.id == user_id).values(language_code=lang_code)
            await session.execute(stmt)
            await session.commit()
