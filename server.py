from flask import Flask, render_template, request, make_response, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, rooms
from flask_cors import CORS

from game_engine import GameEngine
from utils import random_string, refresh_cookies, riffle, return_user_dict, check_team, obfuscate_words, change_host

app = Flask(__name__)
app.secret_key = random_string(24)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins='*')
games = {}


@app.route('/')
def index():
    resp = make_response(render_template('index.html', round_length=GameEngine.ROUND_LENGTH))
    if not request.cookies.get('userID'):
        id = random_string()
        resp.set_cookie('userID', id)
    else:
        cookie = refresh_cookies(request.cookies.get('userID'))
        if cookie != request.cookies.get('userID'):
            resp.set_cookie('userID', cookie)
    return resp


@socketio.on('new_room')
def new_room(data):
    host = data['username']
    room = data['userID']
    games[room] = GameEngine(room)
    games[room].players[request.sid] = return_user_dict(room, host + ' (host)', True)
    join_room(room)
    socketio.emit('new_room_name', {'room': room, 'started': games[room].game_started, 'host': room}, room=request.sid)
    socketio.emit('update_joined_players', ', '.join(games[room].player_names), room=room)
    socketio.emit('set_host', room, room=room)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room'].upper()
    if room in games.keys():
        user = data['userID']
        join_room(room)
        game = games[room]
        game.players[request.sid] = return_user_dict(user, username)
        socketio.emit('player_joined', username + ' has entered ' + room, room=room, broadcast=True)
        socketio.emit('update_joined_players', ', '.join(game.player_names), room=room, broadcast=True)
        socketio.emit('new_room_name', {'room': room,
                                        'started': game.game_started,
                                        'host': game.host}, room=request.sid)
        if game.game_started:
            socketio.emit('receive_word', obfuscate_words(game), room=data['room'])
    else:
        socketio.emit('message', 'Room not found', room=request.sid)


@socketio.on('disconnect')
def disconnect():
    for room in rooms(request.sid):
        if len(room) == 6:
            game = games[room]
            leave_room(room)
            if game.game_started or game.games_played:
                for team in game.teams.keys():
                    if check_team(game, request.sid) == team:
                        player = game.teams[team]['players'].pop(request.sid)
                        if player['host']:
                            change_host(room, games, socketio)
                            return
                        socketio.emit('message',
                                      player['username'] + ' has left the game',
                                      room=room, broadcast=True)
                        break
            if request.sid in game.players.keys():
                player = game.players.pop(request.sid)
                if player['host']:
                    change_host(room, games, socketio)
                    return
                socketio.emit('message', player['username'] + ' has left the game', room=room,
                              broadcast=True)
            socketio.emit('update_joined_players', ', '.join(game.player_names), room=room, broadcast=True)


@socketio.on('start_game')
def start_game(data):
    try:
        game = games[data['room']]
    except KeyError as e:
        socketio.emit('message',
                      'Game ID: ' + str(e) + ' does not exist<br>Please refresh your browser',
                      room=request.sid)
        return

    if not game.game_started:
        if len(game.player_names) > 1 or (game.games_played > 0 and
                                     (len(game.teams['a']['players']) > 0 and
                                      len(game.teams['b']['players']) > 0)):
            game.init_game()
            asids = [sid for sid in game.teams['a']['players'].keys()]
            bsids = [sid for sid in game.teams['b']['players'].keys()]
            teams = {
                'a': [],
                'b': [],
            }
            for sid in asids:
                teams['a'].append(game.teams['a']['players'][sid]['username'])
            for sid in bsids:
                teams['b'].append(game.teams['b']['players'][sid]['username'])
            socketio.emit('game_started', teams, room=data['room'], broadcast=True)
            socketio.emit('start_timer', {'round_length':game.ROUND_LENGTH, 'host': game.host}, room=data['room'],
                          broadcast=True)
            socketio.emit('starting_letter', game.starting_letter, room=data['room'], broadcast=True)
        else:
            socketio.emit('message', 'not enough players', room=data['room'], broadcast=True)


@socketio.on('send_word_to_room')
def send_word_to_room(data):
    try:
        game = games[data['room']]
        if game.game_started:
            team = check_team(game, request.sid)
            if data['word'].lower().startswith(game.starting_letter.lower()):
                game.teams[team]['round_words'].append((data['word'].strip()))
                socketio.emit('receive_word', obfuscate_words(game), room=data['room'], broadcast=True)
        else:
            socketio.emit('message', 'Game not started!', room=request.sid)
    except KeyError:
        socketio.emit('message', 'You are not in a team!', room=request.sid)


@socketio.on('time_up')
def time_up(data):
    game = games[data]
    if game.game_started:
        res = game.end_round()
        res['host'] = game.host
        socketio.emit('round_result', res, room=data, broadcast=True)


@app.route('/files/<path:filename>', methods=['GET'])
def files(filename):
    return send_from_directory('./src/icons/', filename)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7777, debug=True)
