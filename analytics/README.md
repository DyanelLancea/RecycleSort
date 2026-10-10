# Analytics: ResNet50 waste classifier

## Files

| File | What it is |
| --- | --- |
| `cloudmodel.ipynb` | Training notebook (run in local Jupyter, Python 3.12, TensorFlow 2.18.0). Splits the dataset 70/15/15 with seed 42, fine-tunes ResNet50 and EfficientNetB0 (ImageNet weights) and evaluates both on the test split. |
| `evaluate_model.py` | Re-runs the evaluation of the deployed ResNet50 model on a labelled test folder; writes `metrics.json` and a confusion matrix. |
| `results/metrics.json` | Test-set results from the notebook. |
| `results/confusion_matrix_resnet50.png`, `results/confusion_matrix_efficientnetb0.png`, `results/class_distribution.png` | Figures from the notebook. |
| `train_baseline.py` | Trivial majority-class baseline on the synthetic `data/sample_scans.csv` (for comparison only, not a CNN). |
| `requirements.txt` | Python packages for the script and the notebook. |

Dataset source, licence and split: `data/README.md`.

## Results (held-out test split, 1,848 images)

| Model | Accuracy | Macro F1 |
| --- | --- | --- |
| **ResNet50 (deployed)** | **94.86%** | **0.943** |
| EfficientNetB0 | 93.29% | 0.927 |

ResNet50 was chosen because it scored higher on both. Per-class precision, recall and F1 are in `results/metrics.json`; a discussion of errors and limitations is in `evidence/test-data-ai.md`.

## Reproduce

1. Install: `pip install -r analytics/requirements.txt`
2. Put the trained model at `src/app/ml/artefacts/resnet50_final.keras` (Git LFS file in the repository; not in the ZIP because of its size).
3. Run, from the repository root:

```bash
python analytics/evaluate_model.py --dataset data/testing_images --output-dir analytics/results/rerun
```

This writes `analytics/results/rerun/metrics.json` and `confusion_matrix.png`, which should match `results/metrics.json`. Using `--output-dir` keeps the original results untouched.

To retrain from scratch, download the full dataset from the Kaggle link in `data/README.md` and run `cloudmodel.ipynb` top to bottom. Results can differ slightly between runs because training is not fully deterministic (random augmentation and weight updates).
