// Socket connection:
socketio = io('mjfullstack.com:7777');


// DOM elements:

let msgConsole = document.getElementById('msgConsole');
let gameId = document.getElementById('gameIdTag')
let gamePanel = document.getElementById('gamePanel')
let startBtn = document.getElementById('start')
let teamA = document.getElementById('teamA');
let teamB = document.getElementById('teamB');
let roomName = document.getElementById('roomName');
let userName = document.getElementById('userName');
let joinBtn = document.getElementById('join');
let word = document.getElementById('word');
let wordList = document.getElementById('wordList');
let newRoomBtn = document.getElementById('newRoomBtn');
let timer = document.getElementById("timer")

// Socket funcs:

const newRoom = () => {
    socketio.emit('new_room', {userID: getUserIdCookie(), username: userName.value});
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


// Other funcs:

const onEnter = (e, func) => {
    if (e.key === 'Enter') {
        func();
    }
}

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

const convertDateForIos = (date) => {
    let arr = date.split(/[- :]/);
    date = new Date(arr[0], arr[1]-1, arr[2], arr[3], arr[4], arr[5]);
    return date;
}


// Socketio event handling:

socketio.on('connect', () => {
    console.log('Connected');
});

socketio.on('disconnect', () => {
    console.log('Disconnected');
});

socketio.on('message', (msg) => {
    msgConsole.style.display = 'flex';
    msgConsole.innerHTML = msg;
    msgConsole.scrollIntoView(true);
    setTimeout(() => {
        msgConsole.innerHTML = '';
        msgConsole.style.display = 'none';
    }, 3000);
});

socketio.on('player_joined', (msg) => {
    msgConsole.style.display = 'flex';
    msgConsole.innerHTML = msg;
    msgConsole.scrollIntoView(true);
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
    gamePanel.style.display = 'flex';
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
    wordList.innerHTML += `Team A <br> WORDS: ${data.a['good_words'] ? data.a['good_words'] : 'None'}<br>NOT COUNTED: ${data.a['bad_words'] ? data.a['bad_words'] : 'None'}<br>SCORE: ${data.a['score']}`;
    wordList.innerHTML += `<br><br>Team B <br> WORDS: ${data.b['good_words'] ? data.b['good_words'] : 'None'}<br>NOT COUNTED: ${data.b['bad_words'] ? data.b['bad_words'] : 'None'}<br>SCORE: ${data.b['score']}`;
    wordList.innerHTML += `<br><br>COMMON WORDS: ${data.common_words}`;
    wordList.innerHTML += `<br><br>${data.winner}`;
    wordList.innerHTML += `<br>${data.score_tally}`;
    startBtn.style.display = 'block';
});

socketio.on('start_timer', (time) => {
    timer.classList.add('text-2xl', 'font-bold', 'text-center', 'text-red-500')
    timer.innerHTML = 'GO!'
    const countDownDate = convertDateForIos(time).getTime();
    const x = setInterval(function () {
        let now = new Date().getTime();
        let distance = countDownDate - now;
        let seconds = Math.floor((distance % (1000 * 60)) / 1000);
        timer.innerHTML = seconds + "s remaining";
        if (distance < 0) {
            clearInterval(x);
            timer.innerHTML = "TIME'S UP!";
            if (getUserIdCookie() === gameIdTag.innerHTML) {
                socketio.emit('time_up', gameIdTag.innerHTML)
            }
        }
    }, 1000);
});

// DOM event handling:

joinBtn.addEventListener('click', onJoinRoom)

startBtn.addEventListener('click', startGame)

newRoomBtn.addEventListener('click', newRoom)

roomName.addEventListener('keyup', (e) => {
    onEnter(e, onJoinRoom);
});

userName.addEventListener('keyup', (e) => {
    if (roomName.value) {
        onEnter(e, onJoinRoom);
    }
});

word.addEventListener('keyup', (e) => {
    onEnter(e, sendWord);
});

window.onbeforeunload = () => {
    socket.emit('leave', {'user': getUserIdCookie(), 'room': gameId.innerText});
}