from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)

    def __init__(self, telegram_user):
        self.telegram_id = telegram_user.id
        self.username = telegram_user.username
        self.first_name = telegram_user.first_name
        self.last_name = telegram_user.last_name

    def __repr__(self):
        return f'<User {self.username}>'
