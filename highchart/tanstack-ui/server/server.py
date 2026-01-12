"""
TanStack AI Compatible Backend
Streaming SSE endpoint for chart analysis
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[WARN] OpenAI not installed. Run: pip install openai")

app = FastAPI(title="TanStack AI Chart Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client: Optional[AsyncOpenAI] = None
if OPENAI_AVAILABLE:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = AsyncOpenAI(api_key=api_key)

SYSTEM_PROMPT = """Du er en finansanalytiker som analyserer aksjedata visualisert i Highcharts.

Din oppgave er å:
1. ANALYSERE dataene og identifisere viktige mønstre, trender og hendelser
2. FORESLÅ visuelle annotasjoner som hjelper brukeren å forstå dataene
3. SKILLE mellom analyse (summary) og visualisering (annotations/plotBands)

VIKTIGE REGLER:
- Returner KUN gyldig JSON som matcher det spesifiserte skjemaet
- Datoer må være i formatet YYYY-MM-DD
- Ikke foreslå mer enn 5-8 annotasjoner

OUTPUT SCHEMA:
{
  "annotations": [{"point": {"x": "YYYY-MM-DD", "y": <verdi>}, "text": "Beskrivelse", "xOffset": -50, "yOffset": -30}],
  "plotBands": [{"from": "YYYY-MM-DD", "to": "YYYY-MM-DD", "color": "rgba(R,G,B,0.1)", "label": "Beskrivelse"}],
  "plotLines": [{"value": "YYYY-MM-DD", "color": "#hexcolor", "width": 2, "label": "Hendelse"}],
  "summary": "Tekstlig analyse...",
  "confidence": 0.85
}"""


class ChatMessage(BaseModel):
    role: str
    parts: list[dict]


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    data: Optional[dict] = None


def format_sse(data: dict) -> str:
    """Format data as SSE event"""
    return f"data: {json.dumps(data)}\n\n"


async def stream_chat_response(messages: list[ChatMessage]) -> AsyncGenerator[str, None]:
    """Stream chat response using SSE format compatible with TanStack AI"""
    if not client:
        yield format_sse({
            "type": "error",
            "error": "OpenAI API not available"
        })
        return

    # Convert TanStack AI messages to OpenAI format
    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    for msg in messages:
        content = ""
        for part in msg.parts:
            if part.get("type") == "text":
                content += part.get("content", "")
        if content:
            openai_messages.append({"role": msg.role, "content": content})

    try:
        # Start message
        message_id = f"msg_{datetime.now().timestamp()}"
        yield format_sse({
            "type": "message-start",
            "message": {
                "id": message_id,
                "role": "assistant"
            }
        })

        # Stream from OpenAI
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            stream=True,
            temperature=0.7,
            max_tokens=2000
        )

        full_content = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_content += text
                yield format_sse({
                    "type": "text-delta",
                    "delta": text
                })

        # End message
        yield format_sse({
            "type": "message-end",
            "message": {
                "id": message_id,
                "role": "assistant",
                "content": full_content
            }
        })

    except Exception as e:
        yield format_sse({
            "type": "error",
            "error": str(e)
        })


@app.get("/")
async def root():
    return {
        "status": "running",
        "openai_available": client is not None,
        "version": "0.2.0"
    }


@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """SSE streaming endpoint for TanStack AI"""
    return StreamingResponse(
        stream_chat_response(request.messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn
    print("=== TanStack AI Chart Analyzer Backend ===")
    print(f"    OpenAI available: {client is not None}")
    print("    SSE endpoint: http://localhost:8000/api/chat")
    uvicorn.run(app, host="0.0.0.0", port=8000)
