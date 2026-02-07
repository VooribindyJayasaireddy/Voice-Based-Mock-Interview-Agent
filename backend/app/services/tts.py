import requests
import uuid
import edge_tts
import asyncio
import os
from app.core.config import settings

async def elevenlabs_tts(text: str) -> str:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }

    # Ensure audio directory exists
    os.makedirs("audio", exist_ok=True)
    audio_file = f"audio/audio_{uuid.uuid4()}.mp3"

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()  # Raise exception for bad status codes
    
    with open(audio_file, "wb") as f:
        f.write(response.content)

    return audio_file.replace("audio/", "")  # Return just the filename for /audio/ route

async def edge_tts_voice(text: str) -> str:
    # Ensure audio directory exists
    os.makedirs("audio", exist_ok=True)
    audio_file = f"audio/audio_{uuid.uuid4()}.mp3"
    communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
    await communicate.save(audio_file)
    return audio_file.replace("audio/", "")  # Return just the filename for /audio/ route

async def text_to_speech(text: str) -> str:
    if settings.TTS_PROVIDER == "edge":
        return await edge_tts_voice(text)
    return await elevenlabs_tts(text)
