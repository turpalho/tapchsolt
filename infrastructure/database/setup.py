import asyncio
import logging

from sqlalchemy import MetaData, NullPool
from sqlalchemy.ext.asyncio import (AsyncEngine, async_sessionmaker,
                                    create_async_engine)

from .models import Base
from tgbot.config import DbConfig


async def create_db(db: DbConfig, echo: bool = False):
    engine = create_async_engine(
        db.construct_sqlalchemy_url(),
        query_cache_size=1200,
        pool_size=20,
        max_overflow=200,
        future=True,
        echo=echo,
    )

    Base._db_engine = engine
    Base._session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # async with engine.begin() as conn:
    #     # await conn.run_sync(Base.metadata.drop_all)
    #     await conn.run_sync(Base.metadata.create_all)

    # Блок, проверяющий бд на необходимость миграции (проверяет схему бд)
    async with engine.begin() as conn:
        current_metadata = MetaData()
        await conn.run_sync(current_metadata.reflect)

        # Получаем списки имен таблиц из каждого объекта MetaData.
        current_metadata_table_names = list(current_metadata.tables.keys())

        if len(current_metadata.tables) == 0:
            logging.error("Database has no tables. Make init migration")
            await asyncio.sleep(60)
            raise SystemExit

        try:
            current_metadata_table_names.remove('alembic_version')
        except (KeyError, ValueError):
            logging.info("alembic_version table does not exist")

        # Проходимся по каждой таблице и проверяем, что они содержат одинаковые
        # названия колонок.
        for table_name in current_metadata_table_names:
            # Получаем объекты Table для текущих таблиц из каждого объекта
            # MetaData.
            table1 = current_metadata.tables[table_name]
            table2 = Base.metadata.tables[table_name]

            # Получаем списки имен колонок из каждого объекта Table.
            table1_column_names = table1.columns.keys()
            table2_column_names = table2.columns.keys()

            # Сортируем списки имен колонок для упрощения сравнения.
            table1_column_names_sorted = sorted(table1_column_names)
            table2_column_names_sorted = sorted(table2_column_names)

            # Сравниваем списки имен колонок, учитывая их порядок.
            if table1_column_names_sorted != table2_column_names_sorted:
                logging.error("Database schema is not up to date (Table "
                              f"{table_name}). Make migrations")
                await asyncio.sleep(120)
                raise SystemExit

        return engine


async def dispose_db(engine: AsyncEngine):
    await engine.dispose()
