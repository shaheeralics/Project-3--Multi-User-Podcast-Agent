\
from io import BytesIO
from typing import List, Dict, Tuple
from pydub import AudioSegment
from pydub.generators import Silent
import requests
import time

def _line_to_audio(text: str, voice_id: str, eleven_key: str) -> AudioSegment:
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    r = requests.post(
        tts_url,
        headers={
            "xi-api-key": eleven_key,
            "accept": "audio/mpeg",
            "content-type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.8}
        },
        timeout=60
    )
    r.raise_for_status()
    return AudioSegment.from_file(BytesIO(r.content), format="mp3")

def synthesize_episode(script: List[Dict], pause_ms: int, host_voice_id: str, guest_voice_id: str, eleven_key: str) -> Tuple[bytes, str]:
    output = AudioSegment.silent(duration=0)
    gap = Silent(duration=max(0, pause_ms)).to_audio_segment()

    for turn in script:
        speaker = (turn.get("speaker") or "").lower()
        text = turn.get("text") or ""
        if not text.strip():
            continue
        voice_id = host_voice_id if speaker == "host" else guest_voice_id
        seg = _line_to_audio(text, voice_id, eleven_key)
        output += seg + gap
        # gentle rate limit
        time.sleep(0.2)

    buf = BytesIO()
    output.export(buf, format="mp3", bitrate="192k")
    buf.seek(0)
    filename = "episode.mp3"
    return buf.read(), filename
