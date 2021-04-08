import string
from datetime import timedelta, datetime
from itertools import cycle
from random import randint

import enchant

dictionary = enchant.Dict("en_GB")


class GameEngine:
    ROUND_LENGTH = 30
    CHARS = string.ascii_uppercase

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

    def init_game(self):
        if not self._teams:
            self._teams = cycle(self.teams.keys())
            self.sort_teams()
        elif len(self.players):
            self.sort_teams()
        self.starting_letter = self.CHARS[randint(0, len(self.CHARS) - 1)]
        self.game_started = True

    def end_round(self):
        a_res, b_res, a_bad_words, b_bad_words, diff = self.check_words(*self.compare_words())
        a_score, b_score = self.check_scores(a_res, b_res)
        self.teams['a']['round_words'] = []
        self.teams['b']['round_words'] = []
        self.game_started = False
        self.games_played += 1
        if self.check_team_length():
            self.reshuffle_teams()
        return {
            'a': {
                'good_words': ', '.join(a_res),
                'score': str(a_score),
                'bad_words': ', '.join(a_bad_words)
            },
            'b': {
                'good_words': ', '.join(b_res),
                'score': str(b_score),
                'bad_words': ', '.join(b_bad_words)
            },
            'winner': self.return_winner_string(a_score, b_score),
            'score_tally': self.score_string,
            'common_words': ', '.join(list(diff)) if diff else 'None!'
        }

    def sort_teams(self):
        sids = list(self.players.keys())
        for p in sids:
            team = next(self._teams)
            self.teams[team]['players'][p] = self.players.pop(p)

    def check_team_length(self):
        if len(self.teams['a']['players']) + len(self.teams['b']['players']) > 2:
            if len(self.teams['a']['players']) != len(self.teams['b']['players']):
                return True
        elif (len(self.teams['a']['players']) == 0 or len(self.teams['b']['players']) == 0) and len(
                self.teams['a']['players']) + len(self.teams['b']['players']) >= 2:
            return True

    def reshuffle_teams(self):
        for key in self.teams.keys():
            sids = list(self.teams[key]['players'].keys())
            for player in sids:
                self.players[player] = self.teams[key]['players'].pop(player)

    def round_time(self):
        end_time = datetime.now() + timedelta(seconds=self.ROUND_LENGTH + 2)
        return end_time

    def compare_words(self):
        a_words = set([w.title() for w in self.teams['a']['round_words']])
        b_words = set([w.title() for w in self.teams['b']['round_words']])
        a_res, b_res = list(a_words.difference(b_words)), list(b_words.difference(a_words))
        diff = set(list(a_words) + list(b_words)).difference(set(a_res + b_res))
        return a_res, b_res, diff

    def return_winner_string(self, a, b):
        if a > b:
            self.score_tally -= 1
            self.teams['a']['score'] += 1
            return 'Team A won!'
        elif b > a:
            self.score_tally += 1
            self.teams['b']['score'] += 1
            return 'Team B won!'
        elif a == b:
            return 'It was a draw!'

    @staticmethod
    def check_words(a_words, b_words, diff):
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
        return a_words, b_words, a_bad_words, b_bad_words, diff

    @staticmethod
    def check_scores(a_words, b_words):
        a_score = 0
        b_score = 0
        for w in a_words:
            a_score += len(w)
        for w in b_words:
            b_score += len(w)
        return a_score, b_score

    @property
    def score_string(self):
        if self.score_tally < 0:
            return f'Team A is {abs(self.score_tally)} ' \
                   f'{"game" if self.score_tally == -1 else "games"} ' \
                   f'ahead ({self.score_board})'
        elif self.score_tally > 0:
            return f'Team B is {self.score_tally} ' \
                   f'{"game" if self.score_tally == 1 else "games"} ' \
                   f'ahead ({self.score_board})'
        return "The scores are currently level"

    @property
    def player_names(self):
        non_team_players = [player['username'] for player in self.players.values()]
        team_a_players = [player['username'] for player in self.teams['a']['players'].values()]
        team_b_players = [player['username'] for player in self.teams['b']['players'].values()]
        return non_team_players + team_a_players + team_b_players

    @property
    def score_board(self):
        return '-'.join(sorted([str(self.teams['a']['score']), str(self.teams['b']['score'])], reverse=True))
