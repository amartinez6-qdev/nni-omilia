from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .engine import InterpretationError, interpret_tokens
from .models import HealthResponse, InterpretationResponse
from .number_parser import NumberParsingError, parse_transcript
from .transcription import TranscriptionError, WhisperTranscriber


MAX_AUDIO_BYTES = 10 * 1024 * 1024
MODEL_SIZE = os.getenv("WHISPER_MODEL", "tiny")

app = FastAPI(title="Natural Number Interpretation API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

transcriber = WhisperTranscriber(model_size=MODEL_SIZE)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


def _suffix_for_upload(audio: UploadFile) -> str:
    content_type = (audio.content_type or "").lower()
    if "mp4" in content_type or "m4a" in content_type:
        return ".m4a"
    if "ogg" in content_type:
        return ".ogg"
    if "wav" in content_type:
        return ".wav"
    return ".webm"


async def _save_upload(audio: UploadFile) -> Path:
    temporary = tempfile.NamedTemporaryFile(
        prefix="nni-audio-",
        suffix=_suffix_for_upload(audio),
        delete=False,
    )
    path = Path(temporary.name)
    total = 0
    try:
        with temporary:
            while chunk := await audio.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_AUDIO_BYTES:
                    raise HTTPException(status_code=413, detail="Audio file is too large")
                temporary.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await audio.close()
    return path


@app.post("/api/interpret", response_model=InterpretationResponse)
async def interpret(audio: UploadFile = File(...)) -> InterpretationResponse:
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail="An audio file is required")

    path = await _save_upload(audio)
    try:
        try:
            transcription = transcriber.transcribe(path)
            parsed = parse_transcript(transcription.text, transcription.language)
            number, _score, valid = interpret_tokens(parsed.tokens)
        except TranscriptionError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except NumberParsingError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except InterpretationError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

        return InterpretationResponse(
            transcript=transcription.text,
            interpretation=number,
            valid_greek_phone=valid,
        )
    finally:
        path.unlink(missing_ok=True)
