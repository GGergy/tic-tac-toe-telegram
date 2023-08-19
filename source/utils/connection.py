import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.ext import declarative

SqlAlchemyBase = declarative.declarative_base()


def connect(name):
    connection = f'sqlite:///{name.strip()}?check_same_thread=False'
    engine = sqlalchemy.create_engine(connection, echo=False)
    __session_generator = orm.sessionmaker(bind=engine)
    SqlAlchemyBase.metadata.create_all(engine)
    return __session_generator
