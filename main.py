# Real-Time AI Tutor — Sketchpad
# Backend: FastAPI + WebSockets
import os
import asyncio
from typing import Any, Dict, List, AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Optional: If you want to use OpenAI (set OPENAI_API_KEY), we keep a stub here.
USE_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))
# You can wire your preferred model here if desired.

app = FastAPI(title="Real-Time AI Tutor — Sketchpad")
@app.get("/health")
async def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the frontend (static files)


# ---------------------- Demo Orchestrator ----------------------
# For a reliable demo without external API keys, we ship a scripted plan for
# explaining and sketching the Pythagorean theorem. You can replace this with
# your favorite LLM that emits the same "events".
class Event:
    """Small struct-like holder for stream events"""
    def __init__(self, typ: str, payload: Dict[str, Any]):
        self.type = typ
        self.payload = payload


async def pythagorean_script() -> AsyncGenerator[Event, None]:
    """
    Yields a sequence of chat tokens and drawing commands to explain the
    Pythagorean theorem while sketching step-by-step.

    Coordinate system assumes a 800x500 canvas.
    """
    # Intro (streamed as tokens)
    intro = ("Let's explore the Pythagorean theorem with a sketch. "
             "We will draw a right triangle, label its sides, and then relate the areas "
             "of squares on each side to show a² + b² = c².")
    for tok in intro.split(" "):
        yield Event("chat_token", {"token": tok + " "})
        await asyncio.sleep(0.04)

    # Clear and prep canvas (from AI)
    yield Event("draw", {"cmd": "clear"})
    await asyncio.sleep(0.15)

    # Draw right triangle: A(120,380), B(520,380), C(120,140)
    # AB base
    yield Event("draw", {"cmd": "line", "args": {"x1": 120, "y1": 380, "x2": 520, "y2": 380},
                         "style": {"color": "#222222", "width": 3}})
    await asyncio.sleep(0.12)
    # AC vertical
    yield Event("draw", {"cmd": "line", "args": {"x1": 120, "y1": 380, "x2": 120, "y2": 140},
                         "style": {"color": "#222222", "width": 3}})
    await asyncio.sleep(0.12)
    # BC hypotenuse
    yield Event("draw", {"cmd": "line", "args": {"x1": 120, "y1": 140, "x2": 520, "y2": 380},
                         "style": {"color": "#222222", "width": 3}})
    await asyncio.sleep(0.12)

    # Right-angle box
    yield Event("draw", {"cmd": "rect", "args": {"x": 120, "y": 360, "w": 20, "h": 20},
                         "style": {"color": "#222222", "width": 2}})
    await asyncio.sleep(0.1)

    # Labels a, b, c
    yield Event("draw", {"cmd": "text", "args": {"x": 320, "y": 400, "text": "a"},
                         "style": {"color": "#0c6cf2", "width": 2}})
    await asyncio.sleep(0.05)
    yield Event("draw", {"cmd": "text", "args": {"x": 90, "y": 260, "text": "b"},
                         "style": {"color": "#0c6cf2", "width": 2}})
    await asyncio.sleep(0.05)
    yield Event("draw", {"cmd": "text", "args": {"x": 330, "y": 240, "text": "c"},
                         "style": {"color": "#0c6cf2", "width": 2}})
    await asyncio.sleep(0.1)

    # Narration chunk
    t1 = ("Here, the legs are a and b and the hypotenuse is c. "
          "Now we'll draw a square on each leg and a tilted square on the hypotenuse.")
    for tok in t1.split(" "):
        yield Event("chat_token", {"token": tok + " "})
        await asyncio.sleep(0.04)

    # Square on side a (base AB) below the base
    yield Event("draw", {"cmd": "rect", "args": {"x": 120, "y": 380, "w": 400, "h": 140},
                         "style": {"color": "#5a9cff", "width": 2}})
    await asyncio.sleep(0.1)
    yield Event("draw", {"cmd": "text", "args": {"x": 300, "y": 470, "text": "a²"},
                         "style": {"color": "#5a9cff", "width": 2}})
    await asyncio.sleep(0.1)

    # Square on side b (vertical AC) to the left
    yield Event("draw", {"cmd": "rect", "args": {"x": -20, "y": 140, "w": 140, "h": 240},
                         "style": {"color": "#4cd16d", "width": 2}})
    await asyncio.sleep(0.1)
    yield Event("draw", {"cmd": "text", "args": {"x": 30, "y": 260, "text": "b²"},
                         "style": {"color": "#4cd16d", "width": 2}})
    await asyncio.sleep(0.1)

    # Narration chunk
    t2 = ("Finally, we construct a square on the hypotenuse. "
          "Because the hypotenuse is tilted, the square is also tilted.")
    for tok in t2.split(" "):
        yield Event("chat_token", {"token": tok + " "})
        await asyncio.sleep(0.04)

    # Square on hypotenuse (polyline)
    # Compute a rough tilted square using vector perpendicular to BC
    # BC from C(120,140) to B(520,380) => dx=400, dy=240, length ~ 464.76
    # Perp unit vector ~ (-dy, dx)/len = (-240, 400)/~464.76 => scale ~100 for visibility
    pts = [
        {"x": 120, "y": 140},
        {"x": 520, "y": 380},
        {"x": 520 +  -240*0.42, "y": 380 + 400*0.42},
        {"x": 120 +  -240*0.42, "y": 140 + 400*0.42},
    ]
    yield Event("draw", {"cmd": "polyline", "args": {"points": pts, "closed": True},
                         "style": {"color": "#ff8a00", "width": 2}})
    await asyncio.sleep(0.1)
    # label c^2 near center
    cx = (pts[0]["x"] + pts[2]["x"]) / 2
    cy = (pts[0]["y"] + pts[2]["y"]) / 2
    yield Event("draw", {"cmd": "text", "args": {"x": cx, "y": cy, "text": "c²"},
                         "style": {"color": "#ff8a00", "width": 2}})

    # Concluding narration
    t3 = ("The areas of the two leg-squares add up exactly to the area of the hypotenuse-square. "
          "That is, a² plus b² equals c². This is the Pythagorean theorem.")
    for tok in t3.split(" "):
        yield Event("chat_token", {"token": tok + " "})
        await asyncio.sleep(0.04)

    yield Event("chat_message", {"message": "Summary: In any right triangle, a² + b² = c²."})

async def generate_events_for_query(user_text: str) -> AsyncGenerator[Event, None]:
    """Simple router: if user mentions 'pythag' or 'triangle', run the scripted demo;
    otherwise, reply politely and suggest the demo question."""
    u = user_text.lower()
    if "pythag" in u or "triangle" in u or "right triangle" in u:
        async for ev in pythagorean_script():
            yield ev
    else:
        fallback = ("I can demo the Pythagorean theorem with a live sketch. "
                    "Try asking: 'Explain the Pythagorean theorem.'")
        for tok in fallback.split(" "):
            yield Event("chat_token", {"token": tok + " "})
            await asyncio.sleep(0.04)
        yield Event("chat_message", {"message": "Ask about the Pythagorean theorem to see drawing!"})


# ---------------------- WebSocket Endpoint ----------------------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type")
            if msg_type == "user_message":
                text = data.get("text", "")
                # Echo the user's message to UI (optional)
                await ws.send_json({"type": "chat_message", "from": "user", "message": text})

                # Drive AI explanation + drawing (streaming tokens + draw commands)
                async for ev in generate_events_for_query(text):
                    if ev.type == "chat_token":
                        await ws.send_json({"type": "chat_token", **ev.payload})
                    elif ev.type == "chat_message":
                        await ws.send_json({"type": "chat_message", **ev.payload})
                    elif ev.type == "draw":
                        await ws.send_json({"type": "draw", **ev.payload})
                    await asyncio.sleep(0)  # yield
            elif msg_type == "clear_canvas":
                # Forward an explicit clear command (if user presses Clear)
                await ws.send_json({"type": "draw", "cmd": "clear"})
            else:
                # Unknown message types can be ignored or logged
                pass
    except WebSocketDisconnect:
        # Client disconnected; no special cleanup needed for this simple demo
        return

# Mount static files LAST so /ws is not shadowed
app.mount("/", StaticFiles(directory="public", html=True), name="static")
