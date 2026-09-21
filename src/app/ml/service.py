from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model as keras_load_model
from tensorflow.keras.applications.resnet50 import preprocess_input

# Must match the alphabetical order Keras used during training
# (flow_from_directory sorts class folders alphabetically)
CLASSES = (
    "battery", "biological", "cardboard", "clothes", "glass",
    "metal", "paper", "plastic", "shoes", "trash"
)

IMG_SIZE = (224, 224)

# Based on Singapore NEA recycling guidelines: blue bin only accepts
# paper, plastic, glass, metal. Batteries/clothes/shoes need special
# disposal points, not the blue bin. Biological/trash go to general waste.
MATERIAL_INFO = {
    "battery": {
        "recyclable": "special",
        "bin_message": "Batteries don't go in the blue bin! Ask an adult to bring it to a special battery collection point.",
        "fun_fact": "A single battery can pollute up to 167 litres of water if thrown in the trash — that's like a whole bathtub!"
    },
    "biological": {
        "recyclable": "no",
        "bin_message": "Food scraps and plant waste go in the regular trash bin, not recycling.",
        "fun_fact": "Some biological waste can be turned into compost, which helps plants grow — like a superfood for gardens!"
    },
    "cardboard": {
        "recyclable": "yes",
        "bin_message": "Great! Flatten it first, then pop it in the blue recycling bin.",
        "fun_fact": "Recycled cardboard can be turned into new boxes up to 7 times before the fibers get too short to reuse!"
    },
    "clothes": {
        "recyclable": "special",
        "bin_message": "Clothes don't go in the blue bin — look for a special clothing donation or textile recycling box!",
        "fun_fact": "It can take over 700 gallons of water to make just one cotton t-shirt — that's why reusing clothes matters!"
    },
    "glass": {
        "recyclable": "yes",
        "bin_message": "Nice! Glass bottles and jars can go straight into the blue recycling bin.",
        "fun_fact": "Glass can be recycled again and again forever without ever losing its quality!"
    },
    "metal": {
        "recyclable": "yes",
        "bin_message": "Awesome! Rinse it out and place it in the blue recycling bin.",
        "fun_fact": "Recycling one aluminium can saves enough energy to power a TV for about 3 hours!"
    },
    "paper": {
        "recyclable": "yes",
        "bin_message": "Perfect! Clean, dry paper goes in the blue recycling bin.",
        "fun_fact": "Recycling one tonne of paper can save around 17 trees!"
    },
    "plastic": {
        "recyclable": "yes",
        "bin_message": "Good job! Empty and rinse it, then put it in the blue recycling bin.",
        "fun_fact": "A plastic bottle can take up to 450 years to break down in nature — recycling helps a lot!"
    },
    "shoes": {
        "recyclable": "special",
        "bin_message": "Shoes don't go in the blue bin — some shops have special shoe recycling boxes!",
        "fun_fact": "Some old sneakers can be shredded and turned into material for new playground surfaces!"
    },
    "trash": {
        "recyclable": "no",
        "bin_message": "This one goes in the regular trash bin.",
        "fun_fact": "Reducing what we throw away is just as important as recycling — every little bit helps the planet!"
    },
}


@dataclass(frozen=True)
class InferenceResult:
    predicted_class: str
    confidence: float
    is_recyclable: bool
    recyclable_status: str   # "yes", "no", or "special"
    bin_message: str
    fun_fact: str
    model_loaded: bool


def load_model() -> dict:
    """Load the trained ResNet50 artefact when present; otherwise return a mock handle."""
    artefact = Path(__file__).resolve().parent / "artefacts" / "resnet50_final.keras"
    if artefact.exists():
        model = keras_load_model(str(artefact))
        return {"backend": "artefact", "path": str(artefact), "model": model}
    return {"backend": "mock", "path": None, "model": None}


_MODEL = load_model()


def infer(image_bytes: bytes, filename: str = "") -> InferenceResult:
    """Run the real model on an uploaded image and return material + recyclability info."""
    if _MODEL["backend"] != "artefact":
        raise RuntimeError(
            f"Model artefact not found at expected path — check artefacts/resnet50_final.keras exists."
        )

    # Load and preprocess the image
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE)
    img_array = np.array(img, dtype=np.float32)
    img_array = np.expand_dims(img_array, axis=0)  # add batch dimension
    img_array = preprocess_input(img_array)         # ResNet50-specific preprocessing

    # Run inference
    preds = _MODEL["model"].predict(img_array, verbose=0)
    idx = int(np.argmax(preds[0]))
    predicted = CLASSES[idx]
    confidence = round(float(preds[0][idx]), 3)

    info = MATERIAL_INFO[predicted]

    return InferenceResult(
        predicted_class=predicted,
        confidence=confidence,
        is_recyclable=info["recyclable"] == "yes",
        recyclable_status=info["recyclable"],
        bin_message=info["bin_message"],
        fun_fact=info["fun_fact"],
        model_loaded=True,
    )