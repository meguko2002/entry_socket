from pathlib import Path
import logging

basedir = Path(__file__).parent.parent


class BaseConfig:
    SECRET_KEY = "asvmasASFewaasdEWAF"
    WTF_CSRF_SECRET_KEY = "AfaseafasFAEfsadf"


class LocalConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'local.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class TestingConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{basedir / 'testing.sqlite'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


config = {
    "testing": TestingConfig,
    "local": LocalConfig,
}
