socketio = io('mjfullstack.com:7777')

socketio.on('connect', () => {
    console.log('Connected')
})

socketio.on('disconnect', () => {
    console.log('Disconnected')
})

socketio.on('message', (msg) => {
    document.getElementById("timer").innerHTML = msg
    setTimeout(() => {
        document.getElementById("timer").innerHTML = instructions
    }, 3000)
})

socketio.on('player_joined', (msg) => {
    document.getElementById("timer").innerHTML = msg
    setTimeout(() => {
        document.getElementById("timer").innerHTML = instructions
    }, 3000)
})

let gameId = document.getElementById('gameIdTag')
let startBtn = document.getElementById('start')


socketio.on('new_room_name', (data) => {
    gameId.innerHTML = data
    let joinCtrls = document.getElementById('joinCtrls')
    joinCtrls.style.display = 'none'
    startBtn.style.visibility = 'visible'
    document.getElementById("timer").innerHTML = instructions
})

socketio.on('game_started', (data) => {
    loopTeam(data.a.players, teamA);
    loopTeam(data.b.players, teamB);
    wordList.innerHTML = ''
    startBtn.style.visibility = 'hidden';
})

let teamA = document.getElementById('teamA')
let teamB = document.getElementById('teamB')

const loopTeam = (team, teamDiv) => {
    teamDiv.innerHTML = ''
    for (i = 0; i < team.length; i++) {
        let li = document.createElement('li')
        li.innerHTML = team[i][0]
        teamDiv.appendChild(li)
    }
}

let instructions = 'You will have 30 seconds in which to write as many words starting with the starting letter as you can. If your word is the same as a word from the other team, neither word will be counted. Non British-English words (including misspelt words) will not be counted. Proper nouns and names ARE counted (within reason).'

socketio.on('player_rejoined', (data) => {
    loopTeam(data.teams.a.players, teamA);
    loopTeam(data.teams.b.players, teamB);
    wordList.innerHTML = data.teams.a.round_words
})

const getUserIdCookie = () => {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('userID='))
        .split('=')[1]
}

const newRoom = (data) => {
    socketio.emit('new_room', getUserIdCookie());
}

const joinGame = (data) => {
    socketio.emit('join', {username: data.user, userID: getUserIdCookie(), room: data.room});
}
let roomName = document.getElementById('roomName')
let userName = document.getElementById('userName')
let joinBtn = document.getElementById('join')
const onJoinRoom = () => {
    let data = {
        room: roomName.value,
        user: userName.value
    }
    joinGame(data);
}
joinBtn.addEventListener('click', onJoinRoom)
roomName.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
        onJoinRoom()
    }
})

let word = document.getElementById('word')
let wordList = document.getElementById('wordList')

const sendWord = () => {
    socketio.emit('send_word_to_room', {word: word.value, room: gameId.innerText, user: getUserIdCookie()});
    word.value = '';
}
socketio.on('starting_letter', (letter) => {
    document.getElementById('letter').innerHTML = letter
})

const startGame = () => {
    socketio.emit('start_game', {room: gameId.innerText})
}

socketio.on('receive_word', (msg) => {
    console.log('team words: ' + msg)
    // let div = document.createElement('div')
    // div.innerHTML = msg
    // wordList.appendChild(div)
    wordList.innerHTML = msg
})

word.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
        sendWord();
    }
})

const timer = (time) => {
    i = time
    if (i > 0) {
        i--;
    }
}

socketio.on('start_timer', (time) => {


    const countDownDate = new Date(time).getTime();

// Update the count down every 1 second
    const x = setInterval(function () {

        // Get today's date and time
        var now = new Date().getTime();

        // Find the distance between now and the count down date
        var distance = countDownDate - now;

        // Time calculations for days, hours, minutes and seconds
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Display the result in the element with id="demo"
        document.getElementById("timer").innerHTML = seconds + "s remaining";

        // If the count down is finished, write some text
        if (distance < 0) {
            clearInterval(x);
            document.getElementById("timer").innerHTML = "TIME'S UP!";
            if (getUserIdCookie() === gameIdTag.innerHTML) {
                socketio.emit('time_up', gameIdTag.innerHTML)
            }
        }
    }, 1000);
})

socketio.on('round_result', (data) => {
    wordList.innerHTML = ''
    wordList.innerHTML += `Team A <br> WORDS: ${data.a['good_words'] ? data.a['good_words'] : 'None!'}<br>BAD WORDS: ${data.a['bad_words'] ? data.a['bad_words'] : 'None!'}<br>SCORE: ${data.a['score']}`
    wordList.innerHTML += `<br><br>Team B <br> WORDS: ${data.b['good_words'] ? data.b['good_words'] : 'None!'}<br>BAD WORDS: ${data.b['bad_words'] ? data.b['bad_words'] : 'None!'}<br>SCORE: ${data.b['score']}`
    wordList.innerHTML += `<br><br>${data.winner}`
    wordList.innerHTML += `<br><br>COMMON WORDS: ${data.common_words}`
    startBtn.style.visibility = 'visible';
})