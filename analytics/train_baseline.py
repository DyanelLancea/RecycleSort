"""Reproducible baseline on synthetic labels (no neural net)."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sample_scans.csv"
OUT = Path(__file__).resolve().parent / "last_run.json"


def load_rows() -> list[dict[str, str]]:
    with DATA.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    rows = load_rows()
    train = [r for r in rows if r["split"] == "train"]
    test = [r for r in rows if r["split"] == "test"]
    majority = Counter(r["material"] for r in train).most_common(1)[0][0]
    correct = sum(1 for r in test if r["material"] == majority)
    accuracy = correct / len(test) if test else 0.0
    payload = {
        "method": "majority-class baseline on synthetic CSV",
        "majority_class": majority,
        "train_size": len(train),
        "test_size": len(test),
        "accuracy": round(accuracy, 4),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
