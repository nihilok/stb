import itertools
from datetime import datetime, timedelta
from random import randint

import enchant
from flask import Flask, render_template, request, make_response, session
from flask_socketio import SocketIO, join_room, leave_room


def random_string():
    chars = 'WhT21OD9K8CdSX7gU3A0BREjkJYN4PQ5a6s'
    rs = ''
    for i in range(8):
        rs += chars[randint(0, len(chars) - 1)]
    return rs


app = Flask(__name__)
app.secret_key = random_string()
socketio = SocketIO(app, cors_allowed_origins='*')
games = {}


def riffle(deck):
    '''
    Shuffle a list like a deck of cards.
    i.e. given a list, split with second set have the extra if len is odd
    and then interleave, second deck's first item after first deck's first item
    and so on. Thus:
    riffle([1,2,3,4,5,6,7])
    returns [1, 4, 2, 5, 3, 6, 7]
    '''
    cut = len(deck) // 2  # floor division
    deck, second_deck = deck[:cut], deck[cut:]
    for index, item in enumerate(second_deck):
        insert_index = index * 2 + 1
        deck.insert(insert_index, item)
    return deck


class GameEngine:

    ROUND_LENGTH = 30
    CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

    def __init__(self):
        self.players = []
        self.teams = {
            'a': {
                'team_name': '',
                'players': [],
                'round_words': [],
                'score': 0
            },
            'b': {
                'team_name': '',
                'players': [],
                'round_words': [],
                'score': 0
            }
        }
        self._teams = None
        self.game_started = False
        self.starting_letter = ''
        self.games_played = 0

    def init_game(self):
        if not self._teams:
            self._teams = itertools.cycle(self.teams.keys())
        if not self.games_played:
            self.sort_teams()
        elif 1 not in (len(self.teams['a']['players']), len(self.teams['b']['players'])):
            if len(self.teams['a']['players']) % 2 != 0 or len(self.teams['b']['players']) % 2 != 0:
                self.sort_teams()
        self.starting_letter = self.CHARS[randint(0, len(self.CHARS) - 1)]
        self.game_started = True
        self.games_played += 1

    def sort_teams(self):
        for i in range(len(self.players)):
            team = next(self._teams)
            self.teams[team]['players'].append(self.players.pop(-1))

    def round(self):
        """Start timer. When timer ends get all words from players and calculate scores"""
        end_time = datetime.now() + timedelta(seconds=self.ROUND_LENGTH)
        return end_time

    @staticmethod
    def return_winner(a, b):
        if a > b:
            return 'Team A won!'
        elif b > a:
            return 'Team B won!'
        elif a == b:
            return 'It was a draw!'

    def stop_game(self):
        d = enchant.Dict("en_GB")
        self.game_started = False
        a_words = set([w.title() for w in self.teams['a']['round_words']])
        b_words = set([w.title() for w in self.teams['b']['round_words']])
        ares, bres = list(a_words.difference(b_words)), list(b_words.difference(a_words))
        diff = set(list(a_words) + list(b_words)).difference(set(ares + bres))
        self.teams['a']['round_words'] = []
        self.teams['b']['round_words'] = []
        a_bad_words = []
        for word in ares:
            if not d.check(word):
                a_bad_words.append(word)
        for word in a_bad_words:
            ares.remove(word)
        b_bad_words = []
        for word in bres:
            if not d.check(word):
                b_bad_words.append(word)
        for word in b_bad_words:
            bres.remove(word)
        a_score = 0
        b_score = 0
        for w in ares:
            a_score += len(w)
        for w in bres:
            b_score += len(w)

        print('A: ' + ', '.join(ares) + '\nSCORE: ' + str(a_score) + '\nBAD WORDS: ' + ', '.join(a_bad_words))
        print('B: ' + ', '.join(bres) + '\nSCORE: ' + str(b_score) + '\nBAD WORDS: ' + ', '.join(b_bad_words))
        if 1 not in (len(self.teams['a']['players']), len(self.teams['b']['players'])):
            if len(self.teams['a']['players']) % 2 != 0 or len(self.teams['b']['players']) % 2 != 0:
                for key in self.teams.keys():
                    self.players += self.teams[key]['players']
                    self.teams[key]['players'] = []
        return {
            'a': {
                'good_words': ', '.join(ares),
                'score': str(a_score),
                'bad_words': ', '.join(a_bad_words)
            },
            'b': {
                'good_words': ', '.join(bres),
                'score': str(b_score),
                'bad_words': ', '.join(b_bad_words)
            },
            'winner': self.return_winner(a_score, b_score),
            'common_words': ', '.join(list(diff)) if diff else 'None!'
        }


@app.route('/')
def index():
    resp = make_response(render_template('index.html'))
    if not request.cookies.get('userID'):
        id = random_string()
        resp.set_cookie('userID', id)
        session['userID'] = id
    else:
        session['userID'] = request.cookies.get('userID')
    return resp


@app.route('/join')
def join():
    return render_template('join_game.html')


@socketio.on('new_room')
def new_room(data):
    print(data)
    host = data
    room = data
    sock_id = request.sid
    games[room] = GameEngine()
    games[room].players.append(['host', host])
    join_room(room)
    socketio.emit('new_room_name', room, room=room)


@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    if room in games.keys():
        user = data['userID']
        join_room(room)
        game = games[room]
        if user not in [p[1] for p in game.players]:
            game.players.append([username, user])
        else:
            for p in game.players:
                if p[1] == user:
                    p[0] = username
        if game.game_started:
            all_words = riffle(game.teams['a']['round_words'] + game.teams['b']['round_words'])
            socketio.emit('player_rejoined', {'teams': game.teams}, room=room)
            socketio.emit('receive_word', ', '.join(all_words), room=data['room'])
        else:
            socketio.emit('player_joined', username + ' has entered ' + room, room=room, broadcast=True)
        socketio.emit('new_room_name', room, room=room)
    else:
        socketio.emit('message', 'Room not found', room=request.sid)


@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    socketio.emit('message', username + ' has left ' + room, broadcast=True)


@socketio.on('send_word')
def send_word(word):
    socketio.send(word)


@socketio.on('time_up')
def time_up(data):
    game = games[data]
    if game.game_started:
        res = game.stop_game()
        socketio.emit('round_result', res, room=data, broadcast=True)


@socketio.on('start_game')
def start_game(data):
    game = games[data['room']]
    if not game.game_started:
        if len(game.players) > 1 or game.games_played > 0:
            game.init_game()
            socketio.emit('game_started', game.teams, room=data['room'], broadcast=True)
            socketio.emit('start_timer', str(game.round()), room=data['room'], broadcast=True)
            socketio.emit('starting_letter', game.starting_letter, room=data['room'], broadcast=True)
        else:
            socketio.emit('message', 'not enough players', room=data['room'], broadcast=True)


def check_team(instance, user):
    team_a_players = instance.teams['a']['players']
    if user in [p[1] for p in team_a_players]:
        return 'a'
    return 'b'


@socketio.on('send_word_to_room')
def send_word_to_room(data):
    try:
        game = games[data['room']]
        if game.game_started:
            team = check_team(game, data['user'])
            if data['word'].lower().startswith(game.starting_letter.lower()):
                game.teams[team]['round_words'].append(data['word'].strip())
                all_words = riffle(game.teams['a']['round_words'] + game.teams['b']['round_words'])
                ob_words = []
                for word in all_words:
                    ob_word = word[0] + ('*' * (len(word) - 2)) + word[-1]
                    ob_words.append(ob_word)
                socketio.emit('receive_word', ', '.join(ob_words), room=data['room'], broadcast=True)
        else:
            socketio.emit('message', 'Game not started!', room=data['room'])
    except KeyError:
        socketio.emit('message', 'You are not in a game!', room=request.sid)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7777)
