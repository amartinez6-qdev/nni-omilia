# nni-backend

FastAPI service for Natural Number Interpretation.

## Development

```bash
uv sync
uv run uvicorn nni_backend.api:app --reload --port 8000
```

The service exposes `GET /api/health` and `POST /api/interpret`. The latter accepts an audio upload, detects English or Spanish automatically, transcribes it with `faster-whisper`, returns the direct interpretation followed by all deterministic ambiguity variants, and validates every result as a Greek telephone number.

Run backend tests with:

```bash
uv run pytest
```
