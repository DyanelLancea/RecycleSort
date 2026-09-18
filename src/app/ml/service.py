from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

CLASSES = ("paper", "plastic", "metal")
RECYCLABLE = {"paper": True, "plastic": True, "metal": True}


@dataclass(frozen=True)
class InferenceResult:
    predicted_class: str
    confidence: float
    is_recyclable: bool
    model_loaded: bool


def load_model() -> dict:
    """Load a trained artefact when present; otherwise return a mock handle."""
    artefact = Path(__file__).resolve().parent / "artefacts" / "classifier.pt"
    if artefact.exists():
        return {"backend": "artefact", "path": str(artefact)}
    return {"backend": "mock", "path": None}


_MODEL = load_model()


def infer(image_bytes: bytes, filename: str = "") -> InferenceResult:
    """Deterministic mock: class from content hash; recyclable if confidence >= 0.55."""
    digest = hashlib.sha256(image_bytes + filename.encode()).digest()
    idx = digest[0] % len(CLASSES)
    predicted = CLASSES[idx]
    confidence = round(0.55 + (digest[1] / 255.0) * 0.44, 3)
    recyclable = RECYCLABLE[predicted] and confidence >= 0.55
    if b"dirty" in filename.lower().encode() or "dirty" in filename.lower():
        recyclable = False
        confidence = min(confidence, 0.52)
    return InferenceResult(
        predicted_class=predicted,
        confidence=confidence,
        is_recyclable=recyclable,
        model_loaded=_MODEL["backend"] == "artefact",
    )
