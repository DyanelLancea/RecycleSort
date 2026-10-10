# Analytics — ResNet50 model and evaluation

The production classifier is the trained ResNet50 artefact at `src/app/ml/artefacts/resnet50_final.keras`. The API uses this model for inference and maps its ten output indices to the class order listed in `src/app/ml/service.py`.

## Evaluate the trained model

Pass a labelled test-image directory whose immediate subdirectories are the ten class names (`battery`, `biological`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`, `shoes`, and `trash`). Put only held-out test images in this directory; the evaluator does not create or infer a train/test split.

```bash
python analytics/evaluate_model.py --dataset /path/to/labelled-test-images
```

The script loads the model and writes accuracy and per-class precision, recall, F1, and support to `analytics/results/metrics.json`, with a confusion matrix at `analytics/results/confusion_matrix.png`. The dataset path is an argument so the team's actual labelled test set can be supplied by the ML teammate. No evaluation results are included until that run has been performed.

## Reproduce the baseline (synthetic labels only)

From the repository root:

```bash
python analytics/train_baseline.py
```

This separate script:

1. Reads `data/sample_scans.csv`.
2. Fits a trivial majority/rule baseline (not a CNN — a stand-in until images are collected).
3. Prints accuracy on the `test` split.
4. Writes `analytics/last_run.json` with the metrics.

The synthetic majority-class baseline is not a substitute for evaluating the ResNet50 model on the held-out image dataset.
