"use strict";

const socket = io();
let connected = false;
let keystrokeId = 0;
// let timer = null;
const processingQueue = [];

function onSocketConnect () {
  connected = true;
  document.getElementById('status-connected').style.display = 'inline-block';
  document.getElementById('status-disconnected').style.display = 'none';
  document.getElementById('instructions').style.visibility = 'visible';
  document.getElementById('disconnect-reason').style.visibility = 'hidden';
}

function onSocketDisconnect (reason) {
  connected = false;
  document.getElementById('status-connected').style.display = 'none';
  document.getElementById('status-disconnected').style.display = 'inline-block';
  document.getElementById('disconnect-reason').style.visibility = 'visible';
  document.getElementById('disconnect-reason').innerText = 'Error: ' + reason;
  document.getElementById('instructions').style.visibility = 'hidden';
}

function limitRecentKeys (limit) {
  const recentKeysDiv = document.getElementById('recent-keys');
  while (recentKeysDiv.childElementCount > limit) {
    recentKeysDiv.removeChild(recentKeysDiv.firstChild);
  }
}

function addKeyCard (key, keystrokeId) {
  const card = document.createElement('div');
  card.classList.add('key-card');
  if (key === ' ') {
    card.innerHTML = '&nbsp;';
  } else {
    card.innerText = key;
  }
  card.setAttribute('keystroke-id', keystrokeId);
  document.getElementById('recent-keys').appendChild(card);
  limitRecentKeys(10);
}

function updateKeyStatus (keystrokeId, success) {
  const recentKeysDiv = document.getElementById('recent-keys');
  const cards = recentKeysDiv.children;
  for (let i = 0; i < cards.length; i++) {
    const card = cards[i];
    if (parseInt(card.getAttribute('keystroke-id')) === keystrokeId) {
      if (success) {
        card.classList.add('processed-key-card');
      } else {
        card.classList.add('unsupported-key-card');
      }
      return;
    }
  }
}

function onKeyDown (evt) {
  console.log("evt.target.tagName:",evt.target.tagName);
  if (evt.target.tagName === 'INPUT') {
    return; // 如果是向input中输入，则直接返回
  }
  if (!connected) {
    return;
  }
  if (!evt.metaKey) {
    evt.preventDefault();
    addKeyCard(evt.key, keystrokeId);
    processingQueue.push(keystrokeId);
    keystrokeId++;
  }

  let location = null;
  if (evt.location === 1) {
    location = 'left';
  } else if (evt.location === 2) {
    location = 'right';
  }

  socket.emit('keystroke', {
    metaKey: evt.metaKey,
    altKey: evt.altKey,
    shiftKey: evt.shiftKey,
    ctrlKey: evt.ctrlKey,
    key: evt.key,
    keyCode: evt.keyCode,
    location: location,
  });
}

function onKetUp (evt) {
  if (!connected) {
    return;
  }

  let location = null;
  if (evt.location === 1) {
    location = 'left';
  } else if (evt.location === 2) {
    location = 'right';
  }

  socket.emit('key-release', {
    metaKey: evt.metaKey,
    altKey: evt.altKey,
    shiftKey: evt.shiftKey,
    ctrlKey: evt.ctrlKey,
    key: evt.key,
    keyCode: evt.keyCode,
    location: location,
  });
}

function onDisplayHistoryChanged (evt) {
  if (evt.target.checked) {
    document.getElementById('recent-keys').style.visibility = 'visible';
  } else {
    document.getElementById('recent-keys').style.visibility = 'hidden';
    limitRecentKeys(0);
  }
}

function keepKeyDown (direction, code) {
  if (!connected) {
    return;
  }
    addKeyCard(code, keystrokeId);
    processingQueue.push(keystrokeId);
    keystrokeId++;
    console.log('direction:', direction);
    socket.emit('keystroke', {
      metaKey: false,
      altKey: false,
      shiftKey: false,
      ctrlKey: false,
      key: direction,
      keyCode: code,
      location: 0,
    });
}

function clearKeepPress () {
  socket.emit('key-reset');
}

function startRecord () {
  socket.emit('start-record');
}

function saveRecord () {
  const saveFileName = document.getElementById('save-record').value
  socket.emit('save-record', saveFileName);
}

function loadRecording () {
  const loadFileName = document.getElementById('load-record').value
  socket.emit('load-recording', loadFileName);
}

function stopPlayback () {
  socket.emit('stop-playback');
}

function startPlayback () {
  socket.emit('start-playback');
}

document.querySelector('body').addEventListener("keydown", onKeyDown);
document.querySelector('body').addEventListener("keyup", onKetUp);
document.getElementById('display-history-checkbox').addEventListener("change", onDisplayHistoryChanged);
socket.on('connect', onSocketConnect);
socket.on('disconnect', onSocketDisconnect);
socket.on('keystroke-received', (data) => {
  updateKeyStatus(processingQueue.shift(), data.success);
});