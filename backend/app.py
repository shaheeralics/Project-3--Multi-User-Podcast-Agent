\
import os
import io
import json
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from utils.scrape import scrape_and_clean
from utils.script_prompt import build_messages
from utils.audio import synthesize_episode
import requests

# OpenAI client (lazy import to allow missing dependency in local envs)
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

FRONTEND_DIST = os.environ.get("FRONTEND_DIST")

app = Flask(
    __name__,
    static_folder=FRONTEND_DIST,
    static_url_path="/"
) if FRONTEND_DIST and os.path.isdir(FRONTEND_DIST) else Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"})

@app.route("/api/voices", methods=["POST"])
def voices():
    data = request.get_json(force=True)
    eleven_key = data.get("elevenlabs_api_key") or request.headers.get("xi-api-key")
    if not eleven_key:
        return jsonify({"error": "Missing ElevenLabs API key"}), 400
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": eleven_key, "accept": "application/json"}
        )
        if r.status_code >= 400:
            return jsonify({"error": f"ElevenLabs error {r.status_code}", "details": r.text}), 502
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/voice-preview", methods=["POST"])
def voice_preview():
    payload = request.get_json(force=True)
    eleven_key = payload.get("elevenlabs_api_key")
    voice_id = payload.get("voice_id")
    text = payload.get("text") or "G'day! This is a quick voice preview."
    if not eleven_key or not voice_id:
        return jsonify({"error": "Missing elevenlabs_api_key or voice_id"}), 400
    try:
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
        )
        if r.status_code >= 400:
            return jsonify({"error": f"ElevenLabs error {r.status_code}", "details": r.text}), 502
        return send_file(io.BytesIO(r.content), mimetype="audio/mpeg", as_attachment=False, download_name="preview.mp3")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate-script", methods=["POST"])
def generate_script():
    data = request.get_json(force=True)
    url = data.get("url")
    openai_key = data.get("openai_api_key")
    host_name = data.get("host_name", "Host")
    guest_name = data.get("guest_name", "Guest")
    aussie = data.get("aussie", True)
    model = data.get("model") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    if not url or not openai_key:
        return jsonify({"error": "Missing 'url' or 'openai_api_key'"}), 400

    if OpenAI is None:
        return jsonify({"error": "OpenAI client not available in this environment"}), 500

    try:
        article = scrape_and_clean(url)
        client = OpenAI(api_key=openai_key)

        messages = build_messages(
            article_title=article["title"],
            article_text=article["text"],
            host_name=host_name,
            guest_name=guest_name,
            aussie=aussie
        )

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        content = resp.choices[0].message.content
        parsed = json.loads(content)

        return jsonify({
            "article": {"title": article["title"], "url": url},
            "script": parsed.get("script", [])
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate-audio", methods=["POST"])
def generate_audio():
    data = request.get_json(force=True)
    script = data.get("script")
    pause_ms = int(data.get("pause_ms", 400))
    eleven_key = data.get("elevenlabs_api_key")
    host_voice_id = data.get("host_voice_id")
    guest_voice_id = data.get("guest_voice_id")
    if not all([script, eleven_key, host_voice_id, guest_voice_id]):
        return jsonify({"error": "Missing one of required fields: script, elevenlabs_api_key, host_voice_id, guest_voice_id"}), 400
    try:
        mp3_bytes, filename = synthesize_episode(
            script=script,
            pause_ms=pause_ms,
            host_voice_id=host_voice_id,
            guest_voice_id=guest_voice_id,
            eleven_key=eleven_key
        )
        return send_file(io.BytesIO(mp3_bytes), mimetype="audio/mpeg", as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve frontend if built
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if app.static_folder and os.path.isdir(app.static_folder):
        from flask import send_from_directory
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"message": "Frontend not built. API is running."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
