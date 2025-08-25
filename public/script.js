// Real-Time AI Tutor — Sketchpad (frontend)
(function(){
  const chatLog = document.getElementById('chatLog');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const demoBtn = document.getElementById('demoBtn');
  const voiceToggle = document.getElementById('voiceToggle');

  const pad = document.getElementById('pad');
  const ctx = pad.getContext('2d');
  const colorPicker = document.getElementById('colorPicker');
  const widthPicker = document.getElementById('widthPicker');
  const clearBtn = document.getElementById('clearBtn');
  const saveBtn = document.getElementById('saveBtn');

  // --- WebSocket connection ---
let protocol = (location.protocol === 'https:') ? 'wss' : 'ws';
// Use current path as base, e.g. /ai_tutor  (strip trailing slash for consistency)
const basePath = location.pathname.replace(/\/+$/, '');
const ws = new WebSocket(`${protocol}://${location.host}${basePath}/ws`);

  ws.addEventListener('message', (evt) => {
    try {
      const msg = JSON.parse(evt.data);
      handleServerMessage(msg);
    } catch(e) {
      console.error('Bad message', e, evt.data);
    }
  });

  function addMsg(text, who='bot') {
    const div = document.createElement('div');
    div.className = `msg ${who}`;
    const tag = document.createElement('span');
    tag.className = 'tag';
    tag.textContent = who === 'user' ? 'You' : 'Tutor';
    div.appendChild(tag);
    const span = document.createElement('span');
    span.textContent = text;
    div.appendChild(span);
    chatLog.appendChild(div);
    chatLog.scrollTop = chatLog.scrollHeight;
    return span; // return the span to stream tokens into
  }

  // Token streaming buffer for the current bot message
  let currentBotSpan = null;
  function ensureBotSpan() {
    if (!currentBotSpan) {
      currentBotSpan = addMsg('', 'bot');
    }
    return currentBotSpan;
  }

  function endBotSpan() {
    currentBotSpan = null;
  }

  // --- Speech synthesis (optional) ---
  let speakBuffer = '';
  let speakTimer = null;
  function scheduleSpeakFlush() {
    if (!voiceToggle.checked) return;
    if (speakTimer) clearTimeout(speakTimer);
    speakTimer = setTimeout(() => {
      if (speakBuffer.trim().length > 0) {
        const u = new SpeechSynthesisUtterance(speakBuffer);
        window.speechSynthesis.speak(u);
        speakBuffer = '';
      }
    }, 600); // collect tokens a bit before speaking
  }

  function handleServerMessage(msg) {
    if (msg.type === 'chat_message') {
      // finish any streaming span and print full message
      endBotSpan();
      addMsg(msg.message, msg.from === 'user' ? 'user' : 'bot');
      // speak full sentence
      speakBuffer += ' ' + msg.message;
      scheduleSpeakFlush();
    } else if (msg.type === 'chat_token') {
      const span = ensureBotSpan();
      span.textContent += msg.token;
      speakBuffer += msg.token;
      scheduleSpeakFlush();
    } else if (msg.type === 'draw') {
      applyDraw(msg);
    }
  }

  // --- Drawing primitives ---
  function clearCanvas() {
    ctx.clearRect(0, 0, pad.width, pad.height);
  }

  function applyDraw(cmd) {
    if (cmd.cmd === 'clear') {
      clearCanvas();
      return;
    }
    ctx.save();
    const style = cmd.style || {};
    ctx.strokeStyle = style.color || '#FFFFFF';
    ctx.lineWidth = style.width || 2;
    ctx.fillStyle = style.fill || 'transparent';

    if (cmd.cmd === 'line') {
      const {x1,y1,x2,y2} = cmd.args;
      ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke();
    } else if (cmd.cmd === 'rect') {
      const {x,y,w,h} = cmd.args;
      ctx.strokeRect(x,y,w,h);
    } else if (cmd.cmd === 'circle') {
      const {x,y,r} = cmd.args;
      ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.stroke();
    } else if (cmd.cmd === 'polyline') {
      const {points, closed} = cmd.args;
      if (!points || points.length < 2) return;
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i=1;i<points.length;i++) ctx.lineTo(points[i].x, points[i].y);
      if (closed) ctx.closePath();
      ctx.stroke();
    } else if (cmd.cmd === 'text') {
      const {x,y,text} = cmd.args;
      ctx.font = '16px ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial';
      ctx.fillStyle = (cmd.style && cmd.style.color) ? cmd.style.color : '#FFFFFF';
      ctx.fillText(text, x, y);
    }
    ctx.restore();
  }

  // --- User drawing on the canvas ---
  let drawing = false;
  let lastX = 0, lastY = 0;
  function pos(evt) {
    if (evt.touches && evt.touches[0]) {
      const rect = pad.getBoundingClientRect();
      return {
        x: (evt.touches[0].clientX - rect.left) * (pad.width / rect.width),
        y: (evt.touches[0].clientY - rect.top) * (pad.height / rect.height)
      };
    } else {
      const rect = pad.getBoundingClientRect();
      return {
        x: (evt.clientX - rect.left) * (pad.width / rect.width),
        y: (evt.clientY - rect.top) * (pad.height / rect.height)
      };
    }
  }
  function startDraw(evt){
    drawing = true;
    const p = pos(evt);
    lastX = p.x; lastY = p.y;
  }
  function moveDraw(evt){
    if (!drawing) return;
    const p = pos(evt);
    ctx.save();
    ctx.strokeStyle = colorPicker.value;
    ctx.lineWidth = parseInt(widthPicker.value, 10);
    ctx.beginPath(); ctx.moveTo(lastX,lastY); ctx.lineTo(p.x,p.y); ctx.stroke();
    ctx.restore();
    lastX = p.x; lastY = p.y;
  }
  function endDraw(){ drawing = false; }
  pad.addEventListener('mousedown', startDraw);
  pad.addEventListener('mousemove', moveDraw);
  pad.addEventListener('mouseup', endDraw);
  pad.addEventListener('mouseleave', endDraw);
  pad.addEventListener('touchstart', (e)=>{ startDraw(e); e.preventDefault(); });
  pad.addEventListener('touchmove', (e)=>{ moveDraw(e); e.preventDefault(); });
  pad.addEventListener('touchend', (e)=>{ endDraw(); e.preventDefault(); });

  // --- Controls ---
  clearBtn.addEventListener('click', () => {
    clearCanvas();
    // Inform server (optional broadcast-clear)
    ws.send(JSON.stringify({type: 'clear_canvas'}));
  });
  saveBtn.addEventListener('click', () => {
    const url = pad.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sketch.png';
    a.click();
  });

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    // Echo as user message locally for snappy UX
    addMsg(text, 'user');
    ws.send(JSON.stringify({ type: 'user_message', text }));
    chatInput.value = '';
    endBotSpan();
  });

  demoBtn.addEventListener('click', () => {
    const demoQ = "Explain the Pythagorean theorem with a diagram.";
    addMsg(demoQ, 'user');
    ws.send(JSON.stringify({ type: 'user_message', text: demoQ }));
    endBotSpan();
    chatInput.value = '';
  });

  // Nice initial system message
  addMsg("Hi! I'm your real-time AI tutor. Ask about the Pythagorean theorem to see me sketch live.", 'bot');
})();
