from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import AbstractConcreteBase
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.repo.core import BaseCore, T  # noqa


class Base(AbstractConcreteBase, BaseCore):
    create_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now())
    update_date: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now())

    __mapper_args__ = {"eager_defaults": True}

    @property
    def create_date_str(self) -> str:
        return self.create_date.strftime("%d/%m/%Y, %H:%M:%S")
