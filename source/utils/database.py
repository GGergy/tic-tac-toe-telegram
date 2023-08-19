import random

import sqlalchemy.orm
from .user import User
from .room import Room
from .connection import connect


generator = connect('assets/secure/database.db')


def create_user(chat_id, message_id):
    usr = User()
    usr.chat_id = chat_id
    usr.message_id = message_id
    session = generator()
    session.add(usr)
    session.commit()
    session.close()


def user(chat_id, mode='r') -> (User, sqlalchemy.orm.session.Session):
    session = generator()
    usr = session.query(User).get(chat_id)
    if mode == 'r':
        session.close()
        return usr
    return usr, session


def create_room(user_id, room_opened=True):
    rm = Room()
    rm.opened = room_opened
    site = random.randint(1, 2)
    if site == 1:
        rm.cross_site_id = user_id
    else:
        rm.zero_site_id = user_id
    session = generator()
    session.add(rm)
    session.commit()
    session.close()


def get_free_room():
    session = generator()
    rooms = [rm for rm in session.query(Room).all() if (rm.zero_site_id == 0 or rm.cross_site_id == 0) and rm.opened]
    session.close()
    return rooms[0] if rooms else False


def connect_to_room(rm_id: int, user_id: int):
    session = generator()
    rm = session.query(Room).get(rm_id)
    rm.connect(user_id)
    session.commit()
    session.close()


def room(room_id, mode='r') -> (Room, sqlalchemy.orm.session.Session):
    session = generator()
    rm = session.query(Room).get(room_id)
    if mode == 'r':
        session.close()
        return rm
    return rm, session
