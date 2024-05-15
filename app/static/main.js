var socket = io();

socket.on('connect', function () {
    console.log('Connected');
    socket.emit('start_stream');
});

socket.on('log', function(data) {
    var consoleDiv = document.querySelector('.log-console');
    var p = document.createElement('p');
    p.classList.add('console-text')
    p.innerText = data;
    consoleDiv.appendChild(p);
});

socket.on('myport', function(data){
    var horaElement = document.getElementById('myport');
     horaElement.innerText = "" + data;
});

socket.on('whoslead', function(data){
    var horaElement = document.getElementById('currlead');
     horaElement.innerText = "" + data;
});

socket.on('amilead', function(data){
    var horaElement = document.getElementById('amilid');
     horaElement.innerText = "" + data;
});
