import json

import sqlalchemy
from .connection import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    chat_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    message_id = sqlalchemy.Column(sqlalchemy.Integer, default=-1)
    elo = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    room_id = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    matches_won = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    matches_lost = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    matches_played = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    following = sqlalchemy.Column(sqlalchemy.String, default='[]')
    followers = sqlalchemy.Column(sqlalchemy.String, default='[]')

    def get_followers(self):
        return json.loads(self.followers)

    def get_following(self):
        return json.loads(self.following)

    def get_friends(self):
        return list(set(self.get_followers()) & set(self.get_following()))
