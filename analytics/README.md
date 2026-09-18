# Analytics — reproducing the classifier

The production path loads a model artefact from `src/app/ml/`. Until that artefact exists, the API uses **deterministic mock inference** so the web workflow can be demonstrated.

## Reproduce the baseline (synthetic labels)

From the repository root, with the project virtualenv active:

```bash
python analytics/train_baseline.py
```

This script:

1. Reads `data/sample_scans.csv`.
2. Fits a trivial majority/rule baseline (not a CNN — a stand-in until images are collected).
3. Prints accuracy on the `test` split.
4. Writes `analytics/last_run.json` with the metrics.

## Intended real pipeline (not implemented in this stub)

1. Store labelled images in object storage; keep only the manifest in `data/`.
2. Train a supervised image classifier (paper / plastic / metal).
3. Export ONNX or a PyTorch `state_dict` into `src/app/ml/artefacts/`.
4. Point `src/app/ml/service.py` at that file and record evaluation in `evidence/test-data-ai.md`.
