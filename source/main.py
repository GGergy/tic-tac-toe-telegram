import json
import time

import telebot
from telebot import types
from utils import config, database
from utils.callback_io import call_in, call_out, lambda_generator
from utils.room import RoomTypes


bot = telebot.TeleBot(token=config.TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    name = bot.get_chat_member(chat_id=message.chat.id, user_id=message.chat.id).user.full_name
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text='Main menu📋', callback_data=call_out(handler='main', deleting=False)))
    if database.user(chat_id=message.chat.id):
        user, session = database.user(chat_id=message.chat.id, mode='w')
        if user.room_id:
            bot.delete_message(message.chat.id, message.id)
            session.close()
            return
        try:
            bot.delete_message(chat_id=message.chat.id, message_id=user.message_id)
        except telebot.apihelper.ApiTelegramException:
            pass
        mid = bot.send_message(chat_id=message.chat.id, text=f'Welcome, {name}', reply_markup=markup).id
        bot.delete_message(message.chat.id, message.id)
        user.message_id = mid
        session.commit()
        session.close()
        return
    mid = bot.send_message(chat_id=message.chat.id, text=f'Hello, {name}, your profile already created',
                           reply_markup=markup).id
    bot.delete_message(message.chat.id, message.id)
    database.create_user(chat_id=message.chat.id, message_id=mid)


@bot.callback_query_handler(lambda_generator('main'))
def main_menu(call):
    user = database.user(call.message.chat.id)
    if user.room_id:
        return
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Play🎮', callback_data=call_out(handler='play')))
    markup.row(types.InlineKeyboardButton('My profile🌐', callback_data=call_out(handler='profile')))
    markup.row(types.InlineKeyboardButton('About👩🏾‍💻', callback_data=call_out(handler='about')))
    if call_in(call.data).deleting:
        user, session = database.user(call.message.chat.id, mode='w')
        mid = bot.send_message(chat_id=call.message.chat.id, text="It's main menu", reply_markup=markup).id
        user.message_id = mid
        session.commit()
        session.close()
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
        return
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="It's main menu",
                          reply_markup=markup)


@bot.callback_query_handler(lambda_generator('profile'))
def profile(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Followers🤍', callback_data=call_out(handler='followers')))
    markup.row(types.InlineKeyboardButton('Following❤️', callback_data=call_out(handler='following')))
    markup.row(types.InlineKeyboardButton('Friends🤝', callback_data=call_out(handler='friends')))
    markup.row(types.InlineKeyboardButton('World rating🌍', callback_data=call_out('world_rank')))
    markup.row(types.InlineKeyboardButton('back🔙', callback_data=call_out(handler='main', deleting=True)))
    try:
        photo_url = bot.get_user_profile_photos(user_id=call.message.chat.id).photos[0][-1].file_id
    except:
        photo_url = ('https://pushinka.top/uploads/posts/2023-04/1681578786_pushinka-top-p-avatarka'
                     '-stima-vopros-pinterest-1.png')
    name = bot.get_chat_member(chat_id=call.message.chat.id, user_id=call.message.chat.id).user.full_name
    user, session = database.user(chat_id=call.message.chat.id, mode='w')
    mid = bot.send_photo(chat_id=call.message.chat.id, photo=photo_url, reply_markup=markup,
                         caption=f'{name}\nMatches played - {user.matches_played}\nMatches won - {user.matches_won}\n'
                                 f'Matches lost - {user.matches_lost}\nElo - {user.elo}\nFollowers -'
                                 f' {len(user.get_followers())}\nFollowing - {len(user.get_following())}').id
    user.message_id = mid
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    session.commit()
    session.close()


@bot.callback_query_handler(lambda_generator('play'))
def play_menu(call):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Play online🌐', callback_data=call_out(handler='search')))
    markup.row(types.InlineKeyboardButton('Create room➕', callback_data=call_out(handler='create')))
    markup.row(types.InlineKeyboardButton('Connect to room🔗', callback_data=call_out(handler='connect')))
    markup.row(types.InlineKeyboardButton('back🔙', callback_data=call_out(handler='main', deleting=False)))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="It's play menu",
                          reply_markup=markup)


@bot.callback_query_handler(lambda_generator(handler='search'))
def search(call):
    user, session = database.user(call.message.chat.id, 'w')
    if user.room_id:
        return
    user.room_id = 'processing'
    session.commit()
    room = database.get_free_room()
    if room:
        user.room_id = room.room_id
        session.commit()
        session.close()
        database.connect_to_room(room.room_id, call.message.chat.id)
        start_game(room.room_id, call)
        return
    room_id = database.create_room(call.message.chat.id)
    user.room_id = room_id
    session.commit()
    session.close()
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Cancel⛔', callback_data=call_out(handler='cancel_search')))
    bot.edit_message_text(message_id=call.message.id, chat_id=call.message.chat.id,
                          text='Room created, wait for opponent', reply_markup=markup)


def start_game(room_id, call):
    markup = types.InlineKeyboardMarkup()
    markup.row(*[types.InlineKeyboardButton('⬜', callback_data=call_out(handler='move', room=room_id,
                                                                        position=(0, i))) for i in range(3)])
    markup.row(*[types.InlineKeyboardButton('⬜', callback_data=call_out(handler='move', room=room_id,
                                                                        position=(1, i))) for i in range(3)])
    markup.row(*[types.InlineKeyboardButton('⬜', callback_data=call_out(handler='move', room=room_id,
                                                                        position=(2, i))) for i in range(3)])
    room, session = database.room(room_id, 'w')
    room.type = RoomTypes.PLAYING
    player1 = call.message.chat.id
    player2 = room.get_opponent(player1)
    player1_name = bot.get_chat_member(chat_id=player1, user_id=player1).user.full_name
    player2_name = bot.get_chat_member(chat_id=player2, user_id=player2).user.full_name
    user2 = database.user(player2)
    if room.cross_site_id == player1:
        turns = ('Your turn!', "Opponent's turn")
    else:
        turns = ("Opponent's turn", 'Your turn!')
    bot.edit_message_text(text=f'Your opponent - {player2_name}. {turns[0]}', reply_markup=markup, chat_id=player1,
                          message_id=call.message.id)
    bot.edit_message_text(text=f'Your opponent - {player1_name}. {turns[1]}', reply_markup=markup, chat_id=player2,
                          message_id=user2.message_id)
    session.commit()
    session.close()


@bot.callback_query_handler(lambda_generator(handler='move'))
def make_move(call):
    data = call_in(call.data)
    room, session = database.room(data.room, 'w')
    if room.type == RoomTypes.ENDING:
        bot.answer_callback_query(callback_query_id=call.id, text='Game ended')
        session.close()
        return
    move = room.check_move(user_id=call.message.chat.id, position=data.position)
    board = json.loads(room.board)
    if not move:
        bot.answer_callback_query(call.id, "It's not your turn")
    elif move == 'placed':
        bot.answer_callback_query(call.id, "Сell is already occupied")
    else:
        player1 = call.message.chat.id
        player2 = room.get_opponent(player1)
        winner = room.check_end()
        if winner:
            winner, cells = winner
            room.type = RoomTypes.ENDING
            session.commit()
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton(text='Play again🔄', callback_data=call_out(handler='restart_game')))
            markup.row(types.InlineKeyboardButton(text='Cancel⛔', callback_data=call_out(handler='stop_game')))
            user, session1 = database.user(player1, 'w')
            user2, session2 = database.user(player2, 'w')
            messages = ('You win! Elo +10', 'You loose((( Elo -5')
            user.matches_played += 1
            user2.matches_played += 1
            if winner == player1:
                user.elo += 10
                user2.elo -= (5 if user2.elo else 0)
                user.matches_won += 1
                user2.matches_lost += 1
            elif winner == player2:
                user.elo -= (5 if user.elo else 0)
                user2.elo += 10
                user.matches_lost += 1
                user2.matches_won += 1
                messages = messages[::-1]
            else:
                messages = ('Draw!', 'Draw!')
            if cells:
                end_game(cells, user, user2, room, messages)
            bot.edit_message_text(text=messages[0], reply_markup=markup, chat_id=player1, message_id=call.message.id)
            bot.edit_message_text(text=messages[1], reply_markup=markup, chat_id=player2, message_id=user2.message_id)
            session.close()
            session1.commit()
            session1.close()
            session2.commit()
            session2.close()
            return
        player1_name = bot.get_chat_member(chat_id=player1, user_id=player1).user.full_name
        player2_name = bot.get_chat_member(chat_id=player2, user_id=player2).user.full_name
        user2 = database.user(player2)
        markup = types.InlineKeyboardMarkup()
        markup.row(*[types.InlineKeyboardButton(board[0][i],
                                                callback_data=call_out(handler='move', room=data.room,
                                                                       position=(0, i))) for i in range(3)])
        markup.row(*[types.InlineKeyboardButton(board[1][i],
                                                callback_data=call_out(handler='move', room=data.room,
                                                                       position=(1, i))) for i in range(3)])
        markup.row(*[types.InlineKeyboardButton(board[2][i],
                                                callback_data=call_out(handler='move', room=data.room,
                                                                       position=(2, i))) for i in range(3)])
        if move == player1:
            turns = ('Your turn!', "Opponent's turn")
        else:
            turns = ("Opponent's turn", 'Your turn!')
        bot.edit_message_text(text=f'Your opponent - {player2_name}. {turns[0]}', reply_markup=markup, chat_id=player1,
                              message_id=call.message.id)
        bot.edit_message_text(text=f'Your opponent - {player1_name}. {turns[1]}', reply_markup=markup, chat_id=player2,
                              message_id=user2.message_id)
    session.commit()
    session.close()


@bot.callback_query_handler(lambda_generator('cancel_search'))
def cancel_searching(call):
    user, session = database.user(call.message.chat.id, 'w')
    database.close_room(user.room_id)
    user.room_id = 0
    session.commit()
    session.close()
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text='Main menu📋', callback_data=call_out(handler='main', deleting=False)))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Game canceled",
                          reply_markup=markup)


def end_game(cells, user1, user2, room, messages):
    board = json.loads(room.board)
    markup = types.InlineKeyboardMarkup()
    markup.row(*[types.InlineKeyboardButton(board[0][i], callback_data='asd') for i in range(3)])
    markup.row(*[types.InlineKeyboardButton(board[1][i], callback_data='asd') for i in range(3)])
    markup.row(*[types.InlineKeyboardButton(board[2][i], callback_data='asd') for i in range(3)])
    for row, col in cells:
        markup.keyboard[row][col] = types.InlineKeyboardButton("🔥", callback_data="asd")
        bot.edit_message_text(text=messages[0], reply_markup=markup, chat_id=user1.chat_id, message_id=user1.message_id)
        bot.edit_message_text(text=messages[1], reply_markup=markup, chat_id=user2.chat_id, message_id=user2.message_id)
        time.sleep(0.3)
    time.sleep(0.5)


@bot.callback_query_handler(lambda_generator('restart_game'))
def play_again(call):
    user = database.user(call.message.chat.id)
    room, session = database.room(user.room_id, 'w')
    if not room:
        session.close()
        return
    if room.type == RoomTypes.WAITING:
        room.board = json.dumps([['⬜', '⬜', '⬜'], ['⬜', '⬜', '⬜'], ['⬜', '⬜', '⬜']])
        room.zero_site_id, room.cross_site_id = room.cross_site_id, room.zero_site_id
        session.commit()
        start_game(room.room_id, call)
        session.close()
        return
    room.type = RoomTypes.WAITING
    session.commit()
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text='Cancel⛔', callback_data=call_out(handler='stop_game')))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Waiting for your opponent...",
                          reply_markup=markup)
    session.close()


@bot.callback_query_handler(lambda_generator('stop_game'))
def stop_game(call):
    user, sess = database.user(call.message.chat.id, 'w')
    room = database.room(user.room_id)
    if not room:
        sess.close()
        return
    user2, sess2 = database.user(room.get_opponent(user.chat_id), 'w')
    user.room_id = 0
    user2.room_id = 0
    database.close_room(room.room_id)
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text='Main menu📋', callback_data=call_out(handler='main', deleting=False)))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text="Room closed",
                          reply_markup=markup)
    bot.edit_message_text(chat_id=user2.chat_id, message_id=user2.message_id, text="Room closed",
                          reply_markup=markup)
    sess.commit()
    sess.close()
    sess2.commit()
    sess2.close()


@bot.message_handler(content_types=['text', 'audio', 'photo', 'video', 'media', 'file', 'voice', 'video_note'])
def deleter(message):
    bot.delete_message(message.chat.id, message.id)


def main():
    database.close_room()
    print('successful initialize')
    bot.infinity_polling()


if __name__ == '__main__':
    main()
