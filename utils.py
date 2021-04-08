import string
from random import randint


def random_string(string_length=6):
    chars = string.ascii_uppercase + string.digits
    rs = ''
    for i in range(string_length):
        rs += chars[randint(0, len(chars) - 1)]
    return rs


def riffle(deck):
    """
    courtesy of https://stackoverflow.com/a/19899905/14266189
    Shuffle a list like a deck of cards.
    i.e. given a list, split with second set have the extra if len is odd
    and then interleave, second deck's first item after first deck's first item
    and so on. Thus:
    riffle([1,2,3,4,5,6,7])
    returns [1, 4, 2, 5, 3, 6, 7]
    """
    cut = len(deck) // 2  # floor division
    deck, second_deck = deck[:cut], deck[cut:]
    for index, item in enumerate(second_deck):
        insert_index = index * 2 + 1
        deck.insert(insert_index, item)
    return deck


def return_user_dict(user_id, username):
    return {
        'userID': user_id,
        'username': username,
    }


def check_team(instance, sid):
    team_a_players = instance.teams['a']['players']
    if sid in team_a_players.keys():
        return 'a'
    return 'b'


def obfuscate_words(game):
    a_team_words = [(word, 'a') for word in game.teams['a']['round_words']]
    b_team_words = [(word, 'b') for word in game.teams['b']['round_words']]
    all_words = riffle(a_team_words + b_team_words)
    ob_words = []
    for word in all_words:
        _ob_word = word[0][0] + ('*' * (len(word[0]) - 3)) + word[0][-2:]
        ob_words.append((_ob_word, word[1]))
    return ob_words


# refresh old userID cookies which were 8 chars in length:
def refresh_cookies(cookie):
    if len(cookie) > 6:
        return random_string()
    return cookie
