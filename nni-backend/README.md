# nni-backend

FastAPI service for Natural Number Interpretation.

## Development

```bash
uv sync
uv run uvicorn nni_backend.api:app --reload --port 8000
```

The service exposes `GET /api/health` and `POST /api/interpret`. The latter accepts an audio upload, detects English or Spanish automatically, transcribes it with `faster-whisper`, selects the most direct deterministic interpretation, and validates it as a Greek telephone number.

Run backend tests with:

```bash
uv run pytest
```
