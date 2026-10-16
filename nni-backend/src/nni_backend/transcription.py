from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock


class TranscriptionError(RuntimeError):
    """Raised when an audio file cannot be transcribed or uses an unsupported language."""


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str
    language_probability: float


class WhisperTranscriber:
    def __init__(self, model_size: str = "tiny") -> None:
        self.model_size = model_size
        self._model = None
        self._lock = Lock()

    def _get_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from faster_whisper import WhisperModel
                    except ImportError as error:
                        raise TranscriptionError(
                            "faster-whisper is not installed"
                        ) from error
                    self._model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type="int8",
                    )
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        model = self._get_model()
        try:
            segments, info = model.transcribe(
                str(audio_path),
                language=None,
                task="transcribe",
                beam_size=5,
                vad_filter=True,
                condition_on_previous_text=False,
                without_timestamps=True,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as error:  # noqa: BLE001 - convert model errors at the API boundary
            raise TranscriptionError("The audio could not be transcribed") from error

        language = str(getattr(info, "language", "")).lower()
        probability = float(getattr(info, "language_probability", 0.0))
        if language not in {"en", "es"}:
            raise TranscriptionError("Only English and Spanish audio are supported")
        if not text:
            raise TranscriptionError("The audio did not contain speech")

        return TranscriptionResult(
            text=text,
            language=language,
            language_probability=probability,
        )
