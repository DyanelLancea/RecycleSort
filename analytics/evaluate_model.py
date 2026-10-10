"""Evaluate the trained ResNet50 model on a labelled, held-out image folder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

CLASSES = (
    "battery",
    "biological",
    "cardboard",
    "clothes",
    "glass",
    "metal",
    "paper",
    "plastic",
    "shoes",
    "trash",
)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="labelled test-image folder with one subfolder per model class",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "src"
        / "app"
        / "ml"
        / "artefacts"
        / "resnet50_final.keras",
        help="path to the trained .keras model",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "results",
        help="directory for metrics.json and confusion_matrix.png",
    )
    return parser.parse_args()


def collect_images(dataset: Path) -> list[tuple[Path, int]]:
    if not dataset.is_dir():
        raise NotADirectoryError(f"Labelled test-image folder does not exist: {dataset}")

    class_dirs = {path.name for path in dataset.iterdir() if path.is_dir()}
    expected = set(CLASSES)
    if class_dirs != expected:
        missing = sorted(expected - class_dirs)
        extra = sorted(class_dirs - expected)
        raise ValueError(f"Expected exactly the 10 class folders; missing={missing}, extra={extra}")

    samples: list[tuple[Path, int]] = []
    for class_index, class_name in enumerate(CLASSES):
        class_images = sorted(
            path
            for path in (dataset / class_name).rglob("*")
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        )
        if not class_images:
            raise ValueError(f"No supported test images found for class {class_name!r}")
        samples.extend((path, class_index) for path in class_images)
    return samples


def load_image(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        resized = image.convert("RGB").resize(IMAGE_SIZE)
        return np.asarray(resized, dtype=np.float32)


def calculate_metrics(
    true_indices: list[int], predicted_indices: list[int]
) -> tuple[dict[str, object], np.ndarray]:
    matrix = np.zeros((len(CLASSES), len(CLASSES)), dtype=np.int64)
    for true_index, predicted_index in zip(true_indices, predicted_indices, strict=True):
        matrix[true_index, predicted_index] += 1

    per_class: dict[str, dict[str, float | int]] = {}
    for index, class_name in enumerate(CLASSES):
        true_positive = int(matrix[index, index])
        predicted_count = int(matrix[:, index].sum())
        support = int(matrix[index, :].sum())
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / support if support else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        per_class[class_name] = {
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "support": support,
        }

    total = int(matrix.sum())
    accuracy = float(np.trace(matrix)) / total
    return {
        "accuracy": round(accuracy, 6),
        "evaluated_images": total,
        "class_order": list(CLASSES),
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }, matrix


def write_confusion_matrix(matrix: np.ndarray, output_path: Path) -> None:
    cell_size = 48
    left, top = 58, 72
    plot_size = cell_size * len(CLASSES)
    width, height = left + plot_size + 235, top + plot_size + 90
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    max_count = max(1, int(matrix.max()))

    draw.text((left, 18), "Confusion Matrix (held-out test images)", fill="black", font=font)
    draw.text((left + 115, top + plot_size + 48), "Predicted class index", fill="black", font=font)
    draw.text((8, top - 18), "True class index", fill="black", font=font)

    for row in range(len(CLASSES)):
        draw.text((left - 18, top + row * cell_size + 18), str(row + 1), fill="black", font=font)
        for column in range(len(CLASSES)):
            value = int(matrix[row, column])
            intensity = int(245 - 145 * value / max_count)
            x0 = left + column * cell_size
            y0 = top + row * cell_size
            draw.rectangle(
                (x0, y0, x0 + cell_size - 1, y0 + cell_size - 1),
                fill=(intensity, int(intensity + 5), 255),
                outline=(180, 180, 180),
            )
            draw.text((x0 + 18, y0 + 18), str(value), fill="black", font=font)
            if row == 0:
                draw.text((x0 + 20, top - 18), str(column + 1), fill="black", font=font)

    legend_x = left + plot_size + 24
    draw.text((legend_x, top), "Index: class", fill="black", font=font)
    for index, class_name in enumerate(CLASSES):
        draw.text((legend_x, top + 24 + index * 25), f"{index + 1}: {class_name}", fill="black", font=font)

    image.save(output_path)


def main() -> None:
    args = parse_args()
    if not args.model.is_file():
        raise FileNotFoundError(f"Model file does not exist: {args.model}")
    with args.model.open("rb") as handle:
        if handle.readline().startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise ValueError(f"Model path is a Git LFS pointer, not the model file: {args.model}")

    samples = collect_images(args.dataset)

    from tensorflow.keras.applications.resnet50 import preprocess_input
    from tensorflow.keras.models import load_model

    model = load_model(str(args.model))
    true_indices: list[int] = []
    predicted_indices: list[int] = []
    for start in range(0, len(samples), BATCH_SIZE):
        batch = samples[start : start + BATCH_SIZE]
        images = np.stack([load_image(path) for path, _ in batch])
        predictions = model.predict(preprocess_input(images), verbose=0)
        if predictions.ndim != 2 or predictions.shape[1] != len(CLASSES):
            raise ValueError(
                f"Model output must have {len(CLASSES)} class scores per image; "
                f"received shape {predictions.shape}"
            )
        true_indices.extend(class_index for _, class_index in batch)
        predicted_indices.extend(int(index) for index in np.argmax(predictions, axis=1))

    metrics, matrix = calculate_metrics(true_indices, predicted_indices)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "metrics.json"
    confusion_path = args.output_dir / "confusion_matrix.png"
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_confusion_matrix(matrix, confusion_path)
    print(f"Metrics written to {metrics_path}")
    print(f"Confusion matrix written to {confusion_path}")
    print(f"Test accuracy: {metrics['accuracy']:.6f}")


if __name__ == "__main__":
    main()
