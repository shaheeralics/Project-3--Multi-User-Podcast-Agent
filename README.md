# Conversational Podcast Generator (Article → Script → MP3)

A full-stack app that:
1) Scrapes an article URL
2) Uses OpenAI to produce an Aussie-style podcast script (Host ↔ Guest) as JSON
3) Uses ElevenLabs to voice each line and stitches an MP3

## Quickstart (Dev)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# (Optional) cp .env.example .env and edit defaults
python app.py
```

### Frontend
```bash
cd frontend
npm i
npm run dev
```

Open http://localhost:5173 and set your API keys in the UI.

## Production via Docker

```bash
docker build -t podcast-podcaster .
docker run -p 8080:8080 --env OPENAI_MODEL=gpt-4o-mini podcast-podcaster
```

The Flask server hosts the built React app and exposes the API on the same origin.

## Notes

- Keys are provided per request from the frontend; they are not stored on the server.
- Pydub requires ffmpeg. The Dockerfile installs it. On your machine, install ffmpeg if running locally.
- ElevenLabs errors and OpenAI JSON schema errors are surfaced clearly in the UI.
