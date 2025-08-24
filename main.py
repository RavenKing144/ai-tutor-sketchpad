import os
import asyncio
from typing import Any, Dict, AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from openai import AsyncOpenAI

# Setup OpenAI client if key is provided
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI(title="Real-Time AI Tutor — Sketchpad")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------------------- Event Class ----------------------
class Event:
    def __init__(self, typ: str, payload: Dict[str, Any]):
        self.type = typ
        self.payload = payload


# ---------------------- Scripted Demo ----------------------
async def pythagorean_script() -> AsyncGenerator[Event, None]:
    intro = ("Let's explore the Pythagorean theorem with a sketch. "
             "We will draw a right triangle and then relate the areas "
             "of squares on each side to show a² + b² = c².")
    for tok in intro.split(" "):
        yield Event("chat_token", {"token": tok + " "})
        await asyncio.sleep(0.04)

    yield Event("draw", {"cmd": "clear"})
    await asyncio.sleep(0.15)

    # Triangle
    yield Event("draw", {"cmd": "line", "args": {"x1": 120, "y1": 380, "x2": 520, "y2": 380}, "style": {"color": "#222222", "width": 3}})
    yield Event("draw", {"cmd": "line", "args": {"x1": 120, "y1": 380, "x2": 120, "y2": 140}, "style": {"color": "#222222", "width": 3}})
    yield Event("draw", {"cmd": "line", "args": {"x1": 120, "y1": 140, "x2": 520, "y2": 380}, "style": {"color": "#222222", "width": 3}})

    yield Event("draw", {"cmd": "text", "args": {"x": 320, "y": 400, "text": "a"}, "style": {"color": "#0c6cf2", "width": 2}})
    yield Event("draw", {"cmd": "text", "args": {"x": 90, "y": 260, "text": "b"}, "style": {"color": "#0c6cf2", "width": 2}})
    yield Event("draw", {"cmd": "text", "args": {"x": 330, "y": 240, "text": "c"}, "style": {"color": "#0c6cf2", "width": 2}})

    conclusion = "So, in any right triangle, a² + b² = c²."
    for tok in conclusion.split(" "):
        yield Event("chat_token", {"token": tok + " "})
        await asyncio.sleep(0.04)

    yield Event("chat_message", {"message": "Summary: a² + b² = c²"})


# ---------------------- OpenAI Streaming ----------------------
async def generate_from_openai(user_text: str) -> AsyncGenerator[Event, None]:
    if not client:
        return

    stream = await client.chat.completions.create(
        model="gpt-4o-mini",  # You can switch to gpt-4o or gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "You are a helpful tutor. Explain concepts clearly and suggest when to use diagrams."},
            {"role": "user", "content": user_text},
        ],
        stream=True,
    )

    async for event in stream:
        if event.choices[0].delta.content:
            yield Event("chat_token", {"token": event.choices[0].delta.content})
    yield Event("chat_message", {"message": "Done!"})


# ---------------------- Router ----------------------
async def generate_events_for_query(user_text: str):
    if client:
        async for ev in generate_from_openai(user_text):
            yield ev
        return

    if "pythag" in user_text.lower() or "triangle" in user_text.lower():
        async for ev in pythagorean_script():
            yield ev
    else:
        fallback = "Ask about the Pythagorean theorem to see a live drawing demo."
        for tok in fallback.split(" "):
            yield Event("chat_token", {"token": tok + " "})
            await asyncio.sleep(0.04)
        yield Event("chat_message", {"message": fallback})


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
                await ws.send_json({"type": "chat_message", "from": "user", "message": text})

                async for ev in generate_events_for_query(text):
                    if ev.type == "chat_token":
                        await ws.send_json({"type": "chat_token", **ev.payload})
                    elif ev.type == "chat_message":
                        await ws.send_json({"type": "chat_message", **ev.payload})
                    elif ev.type == "draw":
                        await ws.send_json({"type": "draw", **ev.payload})
                    await asyncio.sleep(0)
            elif msg_type == "clear_canvas":
                await ws.send_json({"type": "draw", "cmd": "clear"})
    except WebSocketDisconnect:
        return

# Mount static files last
app.mount("/", StaticFiles(directory="public", html=True), name="static")
