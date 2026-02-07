import subprocess
import uuid
import os
import whisper

WHISPER_MODEL = "small"

async def speech_to_text(audio_bytes: bytes) -> str:
    """
    Uses Whisper Python library instead of CLI to avoid Windows subprocess issues
    """
    
    # 1. Save temp audio file
    audio_file = f"temp_{uuid.uuid4()}.wav"
    with open(audio_file, "wb") as f:
        f.write(audio_bytes)

    try:
        # 2. Load Whisper model and transcribe
        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(audio_file, language="en")
        
        return result["text"].strip()

    finally:
        # 3. Cleanup temp file
        if os.path.exists(audio_file):
            os.remove(audio_file)
