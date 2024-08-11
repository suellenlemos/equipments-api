from sqlalchemy.orm import sessionmaker, Session

from src.config import Db_config


def configure_session() -> Session:
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()
    session.begin()

    return session


def get_engine() -> Session:
    return Db_config.create_default_db_engine()
