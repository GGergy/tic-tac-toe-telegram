import json
import random
import string

import sqlalchemy
from .connection import SqlAlchemyBase


class RoomTypes:
    OPENED = '1'
    CLOSED = '2'
    LOCAL = '3'
    ENDING = '4'
    PLAYING = '5'
    WAITING = '6'


class Room(SqlAlchemyBase):
    __tablename__ = 'rooms'
    room_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    board = sqlalchemy.Column(sqlalchemy.String, default=json.dumps([['⬜', '⬜', '⬜'],
                                                                     ['⬜', '⬜', '⬜'], ['⬜', '⬜', '⬜']]))
    cross_site_id = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    zero_site_id = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    type = sqlalchemy.Column(sqlalchemy.String, default=RoomTypes.OPENED)

    def connect(self, user_id):
        if self.cross_site_id == 0:
            self.cross_site_id = user_id
        else:
            self.zero_site_id = user_id

    def generate_password(self):
        password = ''
        for _ in range(random.randint(10, 15)):
            if random.randint(1, 2) == 1:
                symb = random.choice(string.ascii_letters)
                if random.randint(1, 2) == 1:
                    symb = symb.upper()
            else:
                symb = random.choice(string.digits)
            password += symb
        self.type = password

    def get_opponent(self, user_id):
        if self.cross_site_id == user_id:
            return self.zero_site_id
        return self.cross_site_id

    def check_move(self, user_id, position):
        board = json.loads(self.board)
        if board[position[0]][position[1]] != '⬜':
            return "placed"
        moves = self.get_moves()
        if user_id == self.cross_site_id and moves % 2 == 0:
            board[position[0]][position[1]] = '❌'
            self.board = json.dumps(board)
            return self.zero_site_id
        elif user_id == self.zero_site_id and moves % 2 == 1:
            board[position[0]][position[1]] = '⭕'
            self.board = json.dumps(board)
            return self.cross_site_id
        return False

    def get_moves(self):
        return len([i for item in json.loads(self.board) for i in item if i != "⬜"])

    def check_end(self):
        board = json.loads(self.board)
        for row in range(3):
            if ''.join(board[row]).count('❌') == 3:
                return self.cross_site_id, [(row, i) for i in range(3)]
            if ''.join(board[row]).count('⭕') == 3:
                return self.zero_site_id, [(row, i) for i in range(3)]
        for col in range(3):
            if f"{board[0][col]}{board[1][col]}{board[2][col]}".count('❌') == 3:
                return self.cross_site_id, [(i, col) for i in range(3)]
            if f"{board[0][col]}{board[1][col]}{board[2][col]}".count('⭕') == 3:
                return self.zero_site_id, [(i, col) for i in range(3)]
        if f"{board[0][0]}{board[1][1]}{board[2][2]}".count('❌') == 3:
            return self.cross_site_id, [(i, i) for i in range(3)]
        if f"{board[0][0]}{board[1][1]}{board[2][2]}".count('⭕') == 3:
            return self.zero_site_id, [(i, i) for i in range(3)]
        if f"{board[0][2]}{board[1][1]}{board[2][0]}".count('❌') == 3:
            return self.cross_site_id, [(i, 2 - i) for i in range(3)]
        if f"{board[0][2]}{board[1][1]}{board[2][0]}".count('⭕') == 3:
            return self.zero_site_id, [(i, 2 - i) for i in range(3)]
        if self.get_moves() == 9:
            return 'draw', ()
        return False
