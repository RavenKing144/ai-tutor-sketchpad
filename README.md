# Real-Time AI Tutor — Sketchpad

A product-ready **proof‑of‑concept** that teaches in real time using a collaborative sketchpad. The AI tutor chats with the learner and **sketches step‑by‑step** on a shared canvas, synchronized with its explanation.

> **Timebox assumed:** ~36 hours (within the requested “24–48 hours”).

https://github.com/yourname/ai-tutor-sketchpad (put your repo here after pushing)

---

## ✨ Features

- **Real-time conversation** via WebSockets
- **Synchronized sketching**: the tutor draws primitives (lines/rects/circles/polyline) step-by-step while speaking
- **Low-latency streaming** of tokens to the chat UI for a “live thinking” feel
- **Interactive sketchpad**: learner can draw with color + width, Clear, and Save PNG
- **Optional voice** output in the browser with the Web Speech API
- **No API keys required for the demo** — ships with a scripted lesson on the **Pythagorean theorem**

---

## 🧪 Quickstart

> Requires Python 3.10+

```bash
# 1) Clone and enter
git clone https://github.com/yourname/ai-tutor-sketchpad.git
cd ai-tutor-sketchpad

# 2) Install deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3) Run
uvicorn main:app --reload

# 4) Open
# Visit http://localhost:8000 in your browser
```

**Demo tip:** Click **“Demo Prompt”** or ask: `Explain the Pythagorean theorem` to see the synchronized sketching.

---

## 🧱 Architecture & Design Choices

### High level
```mermaid
flowchart LR
    U[User Browser] <-- WebSocket --> S[FastAPI Server]
    U -- Canvas events --> U
    U -->|HTTP| Static[Static Files (HTML/CSS/JS)]
    S -. Orchestrator .-> LLM[(LLM: optional)]
```

- **Frontend:** Plain HTML/CSS/JS to keep the POC lightweight and easy to run. A single‑page app manages chat, streaming tokens, and an HTML5 canvas sketchpad.
- **Backend:** FastAPI with WebSockets for **low‑latency** bi‑directional messaging. One endpoint `/ws` drives chat and drawing.
- **AI Orchestrator:** For reliability without external keys, the demo uses a **scripted teaching plan** for the Pythagorean theorem that emits a mixed stream of **chat tokens** and **drawing commands**. You can swap this with any LLM that emits the same event protocol.

### Event protocol (server → client)
```jsonc
{ "type": "chat_token",   "token": "streamed token ..." }
{ "type": "chat_message", "message": "final sentence" }
{ "type": "draw", "cmd": "clear" }
{ "type": "draw", "cmd": "line", "args": {"x1":120,"y1":380,"x2":520,"y2":380}, "style": {"color":"#222","width":3} }
{ "type": "draw", "cmd": "rect", "args": {"x":120,"y":380,"w":400,"h":140}, "style": {"color":"#5a9cff","width":2} }
{ "type": "draw", "cmd": "circle", "args": {"x":200,"y":200,"r":40}, "style": {"color":"#aaa","width":2} }
{ "type": "draw", "cmd": "polyline", "args": {"points":[{"x":..,"y":..}, ...], "closed": true}, "style": {"color":"#ff8a00","width":2} }
{ "type": "draw", "cmd": "text", "args": {"x":330,"y":240,"text":"c²"}, "style": {"color":"#ff8a00","width":2} }
```

### Why WebSockets?
- Bi‑directional, low‑latency streaming for both **chat tokens** and **drawing** commands.
- Clean separation of concerns: the **orchestrator** yields an interleaved sequence; the frontend renders it in order.

### Scalability & robustness
- FastAPI’s event loop handles multiple sessions concurrently; upgrade by running with **Uvicorn + workers** behind **NGINX**.
- Protocol is **model‑agnostic**: switch to OpenAI/Gemini/Llama or a local model emitting the same events.
- Add **room IDs** or session routing to support classrooms; persist drawings per room if needed.

---

## 🔌 Optional LLM Integration

This POC ships with a deterministic Pythagorean lesson. To plug an LLM:
1. Replace `generate_events_for_query()` in `main.py` to call your model.
2. Parse your model output into the same event protocol:
   - Stream `chat_token` tokens as they arrive.
   - Emit `draw` commands (line/rect/circle/polyline/text) as the model “decides” to sketch.
3. Consider a **“tool use”** prompt format where the LLM returns JSON drawing actions.

> Tip: Keep drawing **step‑wise** with small time gaps (e.g., 50–150 ms) so it feels natural.

---

## 🖊️ Sketchpad Features

- Lines, rectangles, circles, polylines, and text annotations
- Change **stroke color** & **width**
- **Clear** canvas
- **Save PNG** of the current board
- User can draw freely; AI’s drawing arrives over the socket

---

## 🎓 Chosen Concept: *Pythagorean Theorem*

The demo draws a **right triangle**, labels **a, b, c**, then constructs squares on the two legs and a tilted square on the hypotenuse. The narration and sketch are synchronized to reinforce **a² + b² = c²**.

**Try:** “Explain the Pythagorean theorem with a diagram.”

---

## 📁 Project Structure

```
ai-tutor-sketchpad/
├─ main.py                # FastAPI + WebSocket backend
├─ requirements.txt
├─ public/
│  ├─ index.html          # SPA: chat + canvas UI
│  ├─ styles.css          # clean, modern UI
│  └─ script.js           # socket, drawing primitives, voice
└─ README.md
```

---

## 🧰 Commands

- **Run dev server:** `uvicorn main:app --reload`
- **Change port:** `uvicorn main:app --host 0.0.0.0 --port 8080`
- **Production thinking:** run behind NGINX; scale with multiple Uvicorn workers.

---

## 🧪 Demo Guide (prompts)

- “Explain the **Pythagorean theorem** with a diagram.” ✅ (triggers sketch)
- Ask anything else; the tutor will suggest the Pythagorean demo.

---

## 🔒 Assumptions

- Timebox 36 hours for design, build, and polish.
- No external API keys required for the core demo.
- Browser supports Web Speech API (voice is optional and can be toggled).

---

## 📸 Screenshots / Video (optional)

- Include short 30–120s screen recording of the interaction when you publish the repo.

---

## 📝 License

MIT
