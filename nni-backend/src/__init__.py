from .engine import InterpretationError, interpret_tokens
from .models import InterpretationResponse

__all__ = ["InterpretationError", "InterpretationResponse", "interpret_tokens"]


def main() -> None:
    import uvicorn

    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=False)
