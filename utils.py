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


def return_user_dict(user_id, username, host=False):
    return {
        'userID': user_id,
        'username': username,
        'host': host
    }


def check_team(instance, sid):
    team_a_players = instance.teams['a']['players']
    team_b_players = instance.teams['b']['players']
    if sid in team_a_players.keys():
        return 'a'
    elif sid in team_b_players.keys():
        return 'b'
    return None


def obfuscate_words(game):
    a_team_words = [(word, 'a') for word in game.teams['a']['round_words']]
    b_team_words = [(word, 'b') for word in game.teams['b']['round_words']]
    all_words = riffle(a_team_words + b_team_words)
    ob_words = []
    for word in all_words:
        _ob_word = word[0][0] + ('*' * (len(word[0]) - 3)) + word[0][-2:]
        ob_words.append((_ob_word, word[1]))
    return ob_words


def change_host(room, games, socket):
    game = games[room]
    team_a = game.teams['a']['players']
    team_b = game.teams['b']['players']
    if len(team_a) + len(team_b) > 0:
        if len(team_a) > len(team_b) or (len(team_a) + len(team_b) >= 2 and len(team_a) == len(team_b)):
            new_host_id = list(team_a.items())[0][0]
            game.teams['a']['players'][new_host_id]['host'] = True
            game.teams['a']['players'][new_host_id]['username'] += ' (host)'
            games[room].host = game.teams['a']['players'][new_host_id]['userID']
        else:
            new_host_id = list(team_b.items())[0][0]
            game.teams['b']['players'][new_host_id]['host'] = True
            game.teams['b']['players'][new_host_id]['username'] += ' (host)'
            games[room].host = game.teams['b']['players'][new_host_id]['userID']
    elif len(game.players.keys()):
        new_host_id = list(game.players.items())[0][0]
        game.players[new_host_id]['host'] = True
        game.players[new_host_id]['username'] += ' (host)'
        games[room].host = game.players[new_host_id]['userID']
    else:
        return
    socket.emit('set_host', game.host, room=room, broadcast=True)
    socket.emit('new_room_name', {'room': room, 'started': game.game_started, 'host': game.host}, room=new_host_id)
    socket.emit('message', 'Host disconnected; Host changed', room=room, broadcast=True)
    socket.emit('update_joined_players', ', '.join(game.player_names), room=room, broadcast=True)


# refresh old userID cookies which were 8 chars in length:
def refresh_cookies(cookie):
    if len(cookie) > 6:
        return random_string()
    return cookie
