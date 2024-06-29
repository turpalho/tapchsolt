from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Text, update

from .base import Base

if TYPE_CHECKING:
    from tgbot.config import Config


class ConfigDb(Base):
    __tablename__ = 'config'

    id: Mapped[int] = mapped_column(primary_key=True)
    admins_ids_str: Mapped[str]

    @property
    def admins_tg_ids(self) -> list[int]:
        str_list = self.admins_ids_str.split(",")
        return [int(el) for el in str_list if el.isdigit()]

    @classmethod
    async def create(cls, admins_ids_str: str):
        attrs = {
            "admins_ids_str": admins_ids_str
        }

        cnfg = cls(id=1, **attrs)
        await cls.add(cnfg)

    @classmethod
    async def update_admins_list(cls, admins_ids: list[int]):
        with cls.db_session as session:
            admins_ids_str = ",".join([str(el) for el in admins_ids])
            stmt = update(cls).where(cls.id == 1).values(
                admins_ids_str=admins_ids_str)
            await session.execute(stmt)
            await session.commit()