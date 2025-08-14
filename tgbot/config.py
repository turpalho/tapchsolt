from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Optional

from environs import Env

if TYPE_CHECKING:
    from infrastructure.database.models import ConfigDb


@dataclass
class DbConfig:
    """
    Database configuration class.
    This class holds the settings for the database, such as host, password, port, etc.

    Attributes
    ----------
    host : str
        The host where the database server is located.
    password : str
        The password used to authenticate with the database.
    user : str
        The username used to authenticate with the database.
    database : str
        The name of the database.
    port : int
        The port where the database server is listening.
    """

    host: str
    password: str
    user: str
    database: str
    port: int = 5432

    # For SQLAlchemy
    def construct_sqlalchemy_url(self, driver="asyncpg", host=None, port=None) -> str:
        """
        Constructs and returns a SQLAlchemy URL for this database configuration.
        """
        # TODO: If you're using SQLAlchemy, move the import to the top of the file!
        from sqlalchemy.engine.url import URL

        if not host:
            host = self.host
        if not port:
            port = self.port
        uri = URL.create(
            drivername=f"postgresql+{driver}",
            username=self.user,
            password=self.password,
            host=host,
            port=port,
            database=self.database,
        )
        return uri.render_as_string(hide_password=False)

    @staticmethod
    def from_env(env: Env):
        """
        Creates the DbConfig object from environment variables.
        """
        host = env.str("DB_HOST")
        password = env.str("POSTGRES_PASSWORD")
        user = env.str("POSTGRES_USER")
        database = env.str("DB_NAME")
        port = env.int("POSTGRES_PORT", 5432)
        return DbConfig(host=host, password=password, user=user, database=database, port=port)


@dataclass
class TgBot:
    """
    Creates the TgBot object from environment variables.
    """

    token: str
    bot_name: str
    admin_ids: list[int]
    use_redis: bool
    gemini_api_key: str

    @staticmethod
    def from_env(env: Env):
        """
        Creates the TgBot object from environment variables.
        """
        token = env.str("BOT_TOKEN")
        bot_name = env.str("BOT_NAME")
        admin_ids = env.list("ADMINS", subcast=int)
        use_redis = env.bool("USE_REDIS")
        gemini_api_key = env.str("GEMINI_API_KEY")
        return TgBot(token=token,
                     bot_name=bot_name,
                     admin_ids=admin_ids,
                     use_redis=use_redis,
                     gemini_api_key=gemini_api_key)


@dataclass
class RedisConfig:
    """
    Redis configuration class.

    Attributes
    ----------
    redis_pass : Optional(str)
        The password used to authenticate with Redis.
    redis_port : Optional(int)
        The port where Redis server is listening.
    redis_host : Optional(str)
        The host where Redis server is located.
    """

    redis_pass: Optional[str]
    redis_port: Optional[int]
    redis_host: Optional[str]

    def dsn(self) -> str:
        """
        Constructs and returns a Redis DSN (Data Source Name) for this database configuration.
        """
        if self.redis_pass:
            return f"redis://:{self.redis_pass}@{self.redis_host}:{self.redis_port}/0"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/0"

    @staticmethod
    def from_env(env: Env):
        """
        Creates the RedisConfig object from environment variables.
        """
        redis_pass = env.str("REDIS_PASSWORD")
        redis_port = env.int("REDIS_PORT")
        redis_host = env.str("REDIS_HOST")

        return RedisConfig(redis_pass=redis_pass, redis_port=redis_port, redis_host=redis_host)


@dataclass
class Miscellaneous:
    """
    Miscellaneous configuration class.

    This class holds settings for various other parameters.
    It merely serves as a placeholder for settings that are not part of other categories.

    Attributes
    ----------
    other_params : str, optional
        A string used to hold other various parameters as required (default is None).
    """

    add_admin_cmd: str | None = None
    other_params = None

    @staticmethod
    def from_env(env: Env):
        """
        Creates the Miscellaneous object from environment variables.
        """
        add_admin_cmd = env.str("ADD_ADMIN_CMD")
        return Miscellaneous(add_admin_cmd=add_admin_cmd)


@dataclass
class Config:
    """
    The main configuration class that integrates all the other configuration classes.

    This class holds the other configuration classes, providing a centralized point of access for all settings.

    Attributes
    ----------
    tg_bot : TgBot
        Holds the settings related to the Telegram Bot.
    misc : Miscellaneous
        Holds the values for miscellaneous settings.
    db : Optional[DbConfig]
        Holds the settings specific to the database (default is None).
    redis : Optional[RedisConfig]
        Holds the settings specific to Redis (default is None).
    """

    tg_bot: TgBot
    misc: Miscellaneous
    environment: Literal["dev", "prod"]
    db: Optional[DbConfig] = None
    redis: Optional[RedisConfig] = None

    def synchronize_attrs(self, db_config: "ConfigDb"):
        for attr in db_config.__dict__:
            if attr.startswith("_"):
                continue
            if hasattr(self, attr):
                value = getattr(db_config, attr)
                setattr(self, attr, value)


def load_config(path: str | None = None) -> Config:
    """
    This function takes an optional file path as input and returns a Config object.
    :param path: The path of env file from where to load the configuration variables.
    It reads environment variables from a .env file if provided, else from the process environment.
    :return: Config object with attributes set as per environment variables.
    """

    # Create an Env object.
    # The Env object will be used to read environment variables.
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot.from_env(env),
        db=DbConfig.from_env(env),
        misc=Miscellaneous.from_env(env),
        environment=env.str("ENVIRONMENT", "dev"),
        # redis=RedisConfig.from_env(env),
    )
