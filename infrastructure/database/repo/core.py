from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager
from functools import wraps
from typing import Sequence, Type, TypeVar

from sqlalchemy import MetaData, event, exc, inspect, update
from sqlalchemy import log as sqlalchemy_log
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (AsyncAttrs, AsyncEngine, AsyncSession,
                                    async_sessionmaker)
from sqlalchemy.orm import DeclarativeBase, context
from sqlalchemy.orm.decl_api import DeclarativeAttributeIntercept

sqlalchemy_log._add_default_handler = lambda x: None  # To avoid doubling logs

T = TypeVar('T', bound="BaseCore")

logger = logging.getLogger(__name__)


convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': (
        'fk__%(table_name)s__%(all_column_names)s__'
        '%(referred_table_name)s'
    ),
    'pk': 'pk__%(table_name)s',
}
metadata = MetaData(naming_convention=convention)


def close_session(session: AsyncSession):
    loop = asyncio.get_event_loop()
    loop.create_task(session.close())


async def handle_error(e: Exception, session: AsyncSession):
    await session.rollback()
    raise e


class BaseMeta(type):
    @staticmethod
    def handle_errors(i_func):
        """Errors handling for data-modifying methods"""
        @wraps(i_func)
        async def wrapper(self: "BaseCore", *args, **kwargs):
            try:
                return await i_func(self, *args, **kwargs)
            except (exc.SQLAlchemyError, exc.DBAPIError) as e:
                await handle_error(e, self._db_session)
        return wrapper

    def __new__(cls, name, bases, dct):  # noqa
        for attr_name, attr_value in dct.items():
            if callable(attr_value) and not attr_name.startswith("__"):
                # dct[attr_name] = cls.set_session(attr_value)
                dct[attr_name] = cls.handle_errors(dct[attr_name])
        return super().__new__(cls, name, bases, dct)


class CombinedMeta(DeclarativeAttributeIntercept, BaseMeta):
    pass


class SessionWrapper:
    def __init__(self, session: AsyncSession):
        self.session = session

    def __del__(self):
        close_session(self.session)


def wrapper(session, cls_: Type[BaseCore]):
    @contextmanager
    def get_context():
        try:
            yield session
        finally:
            cls_._sessions_manager.close_session_if_list_is_empty(session)
    return get_context


class GetDbSession:
    def __get__(self, instance: T | None, cls: Type[T]):
        session = getattr(instance, "_db_session", cls._session_maker())

        @contextmanager
        def get_context():
            try:
                yield session
            finally:
                cls._sessions_manager.close_session_if_list_is_empty(session)

        return get_context()


class SessionsManager:
    sessions: dict[AsyncSession, list[int]]

    def __init__(self):
        self.sessions = {}

    def add_obj(self, obj: BaseCore):
        if self.sessions.get(obj._db_session) is None:
            self.sessions[obj._db_session] = []

        self.sessions[obj._db_session].append(id(obj))

    def close_session_if_list_is_empty(self, session: AsyncSession):
        item = self.sessions.get(session)
        if not item:
            close_session(session)
            if item is not None:
                del self.sessions[session]

    def remove_obj(self, obj: BaseCore):
        if hasattr(obj, "_db_session"):
            lst = self.sessions.get(obj._db_session)
            if lst:
                lst.remove(id(obj))
            self.close_session_if_list_is_empty(obj._db_session)


class GetClass:
    """A descriptor that returns a class regardless of whether it is called by
    a class or by an instance of a class
    """

    def __get__(self, instance: T | None, cls: Type[T]):
        if instance:
            return instance.__class__
        else:
            return cls


class BaseCore(AsyncAttrs, DeclarativeBase, metaclass=CombinedMeta):
    metadata = metadata

    _sessions_manager = SessionsManager()
    _cls = GetClass()
    db_session = GetDbSession()

    _db_engine: AsyncEngine
    _session_maker: async_sessionmaker[AsyncSession]

    _db_session: AsyncSession

    @classmethod
    async def get(cls: Type[T], pk) -> T | None:
        """Geg object of the class from db by primary key"""
        with cls.db_session as session:
            result = await session.get(cls, pk)
            return result

    @classmethod
    async def get_one(cls: Type[T], pk) -> T:
        result = await cls.get(pk)
        assert result
        return result

    @classmethod
    async def get_all(cls: Type[T]) -> Sequence[T]:
        stmt = select(cls).order_by(cls.__mapper__.primary_key[0])
        with cls.db_session as db_session:
            result = await db_session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def get_by_attributes(cls: Type[T], **kwargs) -> T:
        stmt = select(cls).filter_by(**kwargs)
        with cls.db_session as db_session:
            result = await db_session.execute(stmt)
            return result.scalars().first()

    @classmethod
    async def get_last(cls: Type[T], **kwargs) -> T:
        with cls.db_session as db_session:
            stmt = select(cls).filter_by(**kwargs).order_by(
                cls.__mapper__.primary_key[0].desc())
            result = await db_session.execute(stmt)
            return result.scalars().first()

    @classmethod
    async def add(cls, value: T) -> T:
        with cls.db_session as db_session:
            value._db_session = db_session
            db_session.add(value)
            await db_session.commit()
            return value

    @classmethod
    async def update(cls, id: int, *args, **kwargs):
        with cls.db_session as session:
            stmt = update(cls).where(cls.id == id).values(**kwargs)
            await session.execute(stmt)
            await session.commit()

    async def add_self(self):
        await self.add(self)

    @classmethod
    async def add_new(cls, *args, **kwargs):
        return await cls.add(cls(*args, **kwargs))

    async def self_delete(self):
        await self._db_session.delete(self)
        await self._db_session.commit()

    @classmethod
    async def execute(cls, stmt):
        with cls.db_session as db_session:
            result = await db_session.execute(stmt)
            return result.scalars().all()

    async def flush(self):
        with self.db_session as db_session:
            await db_session.flush()

    async def commit(self):
        with self.db_session as db_session:
            await db_session.commit()

    async def rollback(self):
        with self.db_session as db_session:
            await db_session.rollback()

    async def expire(self):
        with self.db_session as db_session:
            db_session.expire(self)

    def __del__(self):
        self.__class__._sessions_manager.remove_obj(self)


def my_load_listener(target: BaseCore, context: context.QueryContext):
    state = inspect(target)
    async_session = state.async_session
    if async_session:
        target._db_session = async_session
        target.__class__._sessions_manager.add_obj(target)


event.listen(BaseCore, 'load', my_load_listener, propagate=True)
