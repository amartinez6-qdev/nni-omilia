from pathlib import Path

from fastapi.testclient import TestClient

from nni_backend import api
from nni_backend.transcription import TranscriptionResult


class FakeTranscriber:
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        assert audio_path.exists()
        return TranscriptionResult(
            text="2 10 69 30 6 6 4",
            language="en",
            language_probability=0.99,
        )


def test_health() -> None:
    client = TestClient(api.app)
    assert client.get("/api/health").json() == {"status": "ok"}


def test_interpret_endpoint_returns_all_interpretations(monkeypatch) -> None:
    monkeypatch.setattr(api, "transcriber", FakeTranscriber())
    client = TestClient(api.app)
    response = client.post(
        "/api/interpret",
        files={"audio": ("recording.webm", b"audio", "audio/webm")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "transcript": "2 10 69 30 6 6 4",
        "interpretations": [
            {"number": "2106930664", "valid_greek_phone": True},
            {"number": "210693664", "valid_greek_phone": False},
            {"number": "21060930664", "valid_greek_phone": False},
            {"number": "2106093664", "valid_greek_phone": True},
        ],
    }
