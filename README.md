# Natural Number Interpretation

Small React + FastAPI application for interpreting spoken number sequences and checking whether the selected result is a valid Greek telephone number.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- A browser with microphone support

## Run with one command

From the project root:

```bash
./start.sh
```

Then open the frontend URL printed by the script, normally <http://localhost:5173>.

The script automatically selects the first free backend port starting at `8000` and the first free frontend port starting at `5173`. You can override them with `BACKEND_PORT` and `FRONTEND_PORT`.

The script prepares the backend environment, installs frontend dependencies when needed, and starts both services. If either service exits unexpectedly, the script restarts it automatically after a short delay. Press `Ctrl+C` to stop both services. The `tiny` multilingual Whisper model is downloaded and cached automatically on the first audio request.

Set `RESTART_DELAY_SECONDS` to change the restart delay when needed.

## Manual commands

Backend:

```bash
cd nni-backend
uv sync
uv run uvicorn src.api:app --reload --port 8000
```

Frontend:

```bash
cd nni-frontend
npm ci
npm run dev
```

## Usage

1. Press **Start recording**.
2. Speak a number in English or Spanish.
3. Press **Stop recording**.
4. The audio is submitted automatically.
5. The application displays the transcript and every generated interpretation with its Greek phone-number validity.

The backend detects the language automatically. The direct concatenation is shown first, followed by all deterministic ambiguity variants. Phone validity is reported for every variant and does not change their order.

## API

`POST /api/interpret` accepts an audio multipart field named `audio` and returns:

```json
{
  "transcript": "2 10 69 30 6 6 4",
  "interpretations": [
    {"number": "2106930664", "valid_greek_phone": true},
    {"number": "210693664", "valid_greek_phone": false},
    {"number": "21060930664", "valid_greek_phone": false},
    {"number": "2106093664", "valid_greek_phone": true}
  ]
}
```

`GET /api/health` returns `{ "status": "ok" }`.

## Notes

- The first transcription can take longer while the Whisper model is downloaded and loaded.
- The default `tiny` model favors low startup cost and CPU speed. Set `WHISPER_MODEL=base` before starting the backend when higher transcription quality is preferred.
- Audio is stored only in a temporary file while it is being processed and is deleted afterwards.
- The browser must grant microphone access. For local development, `localhost` is a secure context in modern browsers.
