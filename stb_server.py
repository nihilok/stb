import itertools
from datetime import datetime, timedelta
from random import randint

import enchant
from flask import Flask, render_template, request, make_response, session
from flask_socketio import SocketIO, join_room, leave_room, rooms


def random_string():
    chars = 'WhT21OD9K8CdSX7gU3A0BREjkJYN4PQ5a6s'
    rs = ''
    for i in range(8):
        rs += chars[randint(0, len(chars) - 1)]
    return rs


app = Flask(__name__)
app.secret_key = random_string()
socketio = SocketIO(app, cors_allowed_origins='*')
dictionary = enchant.Dict("en_GB")
games = {}


def riffle(deck):
    """
    Shuffle a list like a deck of cards.
    i.e. given a list, split with second set have the extra if len is odd
    and then interleave, second deck's first item after first deck's first item
    and so on. Thus:
    riffle([1,2,3,4,5,6,7])
    returns [1, 4, 2, 5, 3, 6, 7]
    courtesy of https://stackoverflow.com/a/19899905/14266189
    """
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
        self.players = {}
        self.teams = {
            'a': {
                'team_name': '',
                'players': {},
                'round_words': [],
                'score': 0
            },
            'b': {
                'team_name': '',
                'players': {},
                'round_words': [],
                'score': 0
            }
        }
        self._teams = None
        self.game_started = False
        self.starting_letter = ''
        self.games_played = 0
        self.score_tally = 0  # a negative, b positive

    def check_team_length(self):
        if len(self.teams['a']['players']) + len(self.teams['b']['players']) > 2:
            if len(self.teams['a']['players']) != len(self.teams['b']['players']):
                return True
        elif (len(self.teams['a']['players']) == 0 or len(self.teams['b']['players']) == 0) and len(
                self.teams['a']['players']) + len(self.teams['b']['players']) >= 2:
            return True

    def init_game(self):
        if not self._teams:
            self._teams = itertools.cycle(self.teams.keys())
            self.sort_teams()
        elif self.check_team_length():
            self.sort_teams()
        elif len(self.players):
            self.sort_teams()
        self.starting_letter = self.CHARS[randint(0, len(self.CHARS) - 1)]
        self.game_started = True
        self.games_played += 1

    def sort_teams(self):
        sids = list(self.players.keys())
        for p in sids:
            team = next(self._teams)
            self.teams[team]['players'][p] = self.players.pop(p)

    def round_time(self):
        end_time = datetime.now() + timedelta(seconds=self.ROUND_LENGTH + 2)
        return end_time

    def return_winner(self, a, b):
        if a > b:
            self.score_tally -= 1
            return 'Team A won!'
        elif b > a:
            self.score_tally += 1
            return 'Team B won!'
        elif a == b:
            return 'It was a draw!'

    def parse_score_tally(self):
        if self.score_tally < 0:
            return f'Team A has won {abs(self.score_tally)} more {"game" if self.score_tally == 1 else "games"} than Team B'
        elif self.score_tally > 0:
            return f'Team B has won {self.score_tally} more {"game" if self.score_tally == 1 else "games"} than Team A'
        return "The scores are currently level"

    @staticmethod
    def check_words(a_words, b_words):
        a_bad_words = []
        for word in a_words:
            if not dictionary.check(word):
                a_bad_words.append(word)
        for word in a_bad_words:
            a_words.remove(word)
        b_bad_words = []
        for word in b_words:
            if not dictionary.check(word):
                b_bad_words.append(word)
        for word in b_bad_words:
            b_words.remove(word)
        return a_words, b_words, a_bad_words, b_bad_words

    @staticmethod
    def check_scores(a_words, b_words):
        a_score = 0
        b_score = 0
        for w in a_words:
            a_score += len(w)
        for w in b_words:
            b_score += len(w)
        return a_score, b_score

    def stop_game(self):
        a_words = set([w.title() for w in self.teams['a']['round_words']])
        b_words = set([w.title() for w in self.teams['b']['round_words']])
        ares, bres = list(a_words.difference(b_words)), list(b_words.difference(a_words))
        diff = set(list(a_words) + list(b_words)).difference(set(ares + bres))
        ares, bres, a_bad_words, b_bad_words = self.check_words(ares, bres)
        a_score, b_score = self.check_scores(ares, bres)
        if self.check_team_length():
            for key in self.teams.keys():
                sids = list(self.teams[key]['players'].keys())
                for player in sids:
                    self.players[player] = self.teams[key]['players'].pop(player)
                self.teams[key]['players'] = {}
        self.teams['a']['round_words'] = []
        self.teams['b']['round_words'] = []
        self.game_started = False
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
            'score_tally': self.parse_score_tally(),
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


def return_user_dict(user_id, username):
    return {
        'userID': user_id,
        'username': username,
    }


@socketio.on('new_room')
def new_room(data):
    host = data['username']
    room = data['userID']
    games[room] = GameEngine()
    games[room].players[request.sid] = return_user_dict(room, host + ' (host)')
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
        game.players[request.sid] = return_user_dict(user, username)
        socketio.emit('player_joined', username + ' has entered ' + room, room=room, broadcast=True)
        if game.game_started:
            all_words = riffle(game.teams['a']['round_words'] + game.teams['b']['round_words'])
            socketio.emit('receive_word', ', '.join(all_words), room=data['room'])
        socketio.emit('new_room_name', room, room=room)
    else:
        socketio.emit('message', 'Room not found', room=request.sid)


@socketio.on('disconnect')
def disconnect():
    game = None
    _room = None
    for room in rooms(request.sid):
        leave_room(room)
        if len(room) == 8:
            game = games[room]
            _room = room
    if game:
        if game.game_started or game.games_played:
            for team in game.teams.keys():
                if request.sid in game.teams[team]['players'].keys():
                    socketio.emit('message',
                                  game.teams[team]['players'].pop(request.sid)['username'] + ' has left the game',
                                  room=_room, broadcast=True)
                    break
        if request.sid in game.players.keys():
            socketio.emit('message', game.players.pop(request.sid)['username'] + ' has left the game', room=_room,
                          broadcast=True)


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
        if len(game.players) > 1 or (game.games_played > 0 and
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
            socketio.emit('start_timer', game.round_time().strftime('%Y-%m-%d %H:%M:%S'), room=data['room'],
                          broadcast=True)
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
            socketio.emit('message', 'Game not started!', room=request.sid)
    except KeyError:
        socketio.emit('message', 'You are not in a game!', room=request.sid)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7777)
