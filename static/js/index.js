let instructions = 'You will have 30 seconds in which to write as many words starting with the starting letter as you can. If your word is the same as a word from the other team, neither word will be counted. Non British-English words (including misspelt words) will not be counted. Proper nouns and names ARE counted (within reason).';
let msgConsole = document.getElementById('msgConsole');
let gameId = document.getElementById('gameIdTag')
let startBtn = document.getElementById('start')
let teamA = document.getElementById('teamA');
let teamB = document.getElementById('teamB');
let roomName = document.getElementById('roomName');
let userName = document.getElementById('userName');
let joinBtn = document.getElementById('join');
let word = document.getElementById('word');
let wordList = document.getElementById('wordList');
let newRoomBtn = document.getElementById('newRoomBtn');

const getUserIdCookie = () => {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('userID='))
        .split('=')[1];
};

const loopTeam = (team, teamDiv) => {
    teamDiv.innerHTML = '';
    for (i = 0; i < team.length; i++) {
        let li = document.createElement('li');
        li.innerHTML = team[i][0];
        teamDiv.appendChild(li);
    }
};

const newRoom = () => {
    socketio.emit('new_room', getUserIdCookie());
};

const joinGame = (data) => {
    socketio.emit('join', {username: data.user, userID: getUserIdCookie(), room: data.room});
};

const onJoinRoom = () => {
    let data = {
        room: roomName.value,
        user: userName.value
    };
    joinGame(data);
};

const sendWord = () => {
    socketio.emit('send_word_to_room', {word: word.value, room: gameId.innerText, user: getUserIdCookie()});
    word.value = '';
};

const startGame = () => {
    socketio.emit('start_game', {room: gameId.innerText});
};

const onEnter = (e, func) => {
    if (e.key === 'Enter') {
        func();
    }
}

// Socketio events:
socketio = io('mjfullstack.com:7777');

socketio.on('connect', () => {
    console.log('Connected');
});

socketio.on('disconnect', () => {
    console.log('Disconnected');
});

socketio.on('message', (msg) => {
    window.scrollTo(0, 0);
    msgConsole.style.display = 'block';
    msgConsole.innerHTML = msg;
    setTimeout(() => {
        msgConsole.innerHTML = '';
        msgConsole.style.display = 'none';
    }, 3000);
});

socketio.on('player_joined', (msg) => {
    msgConsole.style.display = 'block';
    msgConsole.innerHTML = msg;
    setTimeout(() => {
        msgConsole.innerHTML = '';
        msgConsole.style.display = 'none';
    }, 3000);
});

socketio.on('new_room_name', (data) => {
    gameId.innerHTML = data;
    let joinCtrls = document.getElementById('joinCtrls');
    joinCtrls.style.display = 'none';
    startBtn.style.display = 'block';
    document.getElementById("timer").innerHTML = instructions;
});

socketio.on('game_started', (data) => {
    loopTeam(data.a.players, teamA);
    loopTeam(data.b.players, teamB);
    wordList.innerHTML = '';
    startBtn.style.display = 'none';
});

socketio.on('player_rejoined', (data) => {
    loopTeam(data.teams.a.players, teamA);
    loopTeam(data.teams.b.players, teamB);
    wordList.innerHTML = data.teams.a.round_words;
});

socketio.on('starting_letter', (letter) => {
    document.getElementById('letter').innerHTML = letter;
});

socketio.on('receive_word', (msg) => {
    console.log('team words: ' + msg);
    wordList.innerHTML = msg;
});

socketio.on('round_result', (data) => {
    wordList.innerHTML = '';
    wordList.innerHTML += `Team A <br> WORDS: ${data.a['good_words'] ? data.a['good_words'] : 'None!'}<br>NOT COUNTED: ${data.a['bad_words'] ? data.a['bad_words'] : 'None!'}<br>SCORE: ${data.a['score']}`;
    wordList.innerHTML += `<br><br>Team B <br> WORDS: ${data.b['good_words'] ? data.b['good_words'] : 'None!'}<br>NOT COUNTED: ${data.b['bad_words'] ? data.b['bad_words'] : 'None!'}<br>SCORE: ${data.b['score']}`;
    wordList.innerHTML += `<br><br>${data.winner}`;
    wordList.innerHTML += `<br>${data.score_tally}`;
    wordList.innerHTML += `<br><br>COMMON WORDS: ${data.common_words}`;
    startBtn.style.display = 'block';
});

socketio.on('start_timer', (time) => {
    const countDownDate = new Date(time).getTime();
    const x = setInterval(function () {
        var now = new Date().getTime();
        var distance = countDownDate - now;
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        document.getElementById("timer").innerHTML = seconds + "s remaining";
        if (distance < 0) {
            clearInterval(x);
            document.getElementById("timer").innerHTML = "TIME'S UP!";
            if (getUserIdCookie() === gameIdTag.innerHTML) {
                socketio.emit('time_up', gameIdTag.innerHTML)
            }
        }
    }, 1000);
});

// DOM events
joinBtn.addEventListener('click', onJoinRoom)

startBtn.addEventListener('click', startGame)

newRoomBtn.addEventListener('click', newRoom)

roomName.addEventListener('keyup', (e) => {
    onEnter(e, onJoinRoom);
});

word.addEventListener('keyup', (e) => {
    onEnter(e, sendWord);
});
