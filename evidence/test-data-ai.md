# Test 3: Data and AI validation

- **Objective:** Show that the deployed ResNet50 classifier gives correct, interpretable results (a) on the full held-out test set and (b) through the live cloud service, and record its limitations.
- **Setup:**
  - Model: ResNet50 (ImageNet weights, fine-tuned), 10 classes, file `src/app/ml/artefacts/resnet50_final.keras`, served from S3 to `rs-app-asg` (2 x t3.medium) behind `rs-alb`.
  - Training notebook: `analytics/cloudmodel.ipynb` (TensorFlow 2.18.0, Python 3.12).
  - Dataset: 12,259 labelled images in 10 classes, split 70/15/15 with seed 42 (train 8,578, validation 1,833, test 1,848). Source and licence: `https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2?select=original, MIT` (see `data/README.md`).
  - Held-out test images: `data/testing_images/` (1,848 images, never used for training).
  - Repository commit `0ad07bb`.
- **Command/steps:**
  - **Part A (offline, full test set):** `analytics/cloudmodel.ipynb`, cell 19, evaluates both trained models on all 1,848 test images. Results saved to `analytics/results/metrics.json`, `analytics/results/confusion_matrix_resnet50.png`, `analytics/results/confusion_matrix_efficientnetb0.png`.
  - **Part B (live, through the cloud service):** from AWS CloudShell, one test image per class was taken from `data/testing_images/<class>/` and uploaded to `POST /api/upload` on the ALB. Commands and output: `evidence/raw/test3-live-output.txt`.
- **Expected result:** Test-set accuracy clearly above the majority-class baseline (`analytics/train_baseline.py`) with balanced per-class scores; live predictions match the true class and return within a few seconds.

## Actual result: Part A (1,848 held-out test images)

| Model | Test accuracy | Macro F1 |
| --- | --- | --- |
| **ResNet50 (deployed)** | **94.86%** | **0.943** |
| EfficientNetB0 (compared) | 93.29% | 0.927 |
| Majority-class baseline (always "clothes") | about 15% (285 / 1,848) | n/a |

ResNet50 per class (from `analytics/results/metrics.json`):

| Class | Precision | Recall | F1 | Test images |
| --- | --- | --- | --- | --- |
| battery | 0.96 | 0.96 | 0.96 | 114 |
| biological | 0.98 | 1.00 | 0.99 | 106 |
| cardboard | 0.96 | 0.94 | 0.95 | 213 |
| clothes | 0.99 | 0.99 | 0.99 | 285 |
| glass | 0.93 | 0.94 | 0.94 | 261 |
| metal | 0.86 | 0.94 | 0.90 | 140 |
| paper | 0.92 | 0.89 | 0.90 | 201 |
| plastic | 0.95 | 0.93 | 0.94 | 241 |
| shoes | 1.00 | 0.98 | 0.99 | 218 |
| trash | 0.87 | 0.87 | 0.87 | 69 |

Main confusions (`analytics/results/confusion_matrix_resnet50.png`): cardboard predicted as paper (9 images), plastic predicted as glass (8), glass predicted as plastic (6), paper predicted as trash (6). ResNet50 was chosen over EfficientNetB0 because it scored higher on every summary metric, at the cost of a larger file (225 MB vs 42 MB) and slower inference.

## Actual result: Part B (live service, 10 held-out images)

| True class | Predicted | Confidence | Correct | Response time (s) |
| --- | --- | --- | --- | --- |
| battery | battery | 0.972 | yes | 10.78 (first request on that server, model loading) |
| biological | biological | 0.950 | yes | 0.20 |
| cardboard | cardboard | 1.000 | yes | 0.26 |
| clothes | clothes | 1.000 | yes | 0.28 |
| glass | glass | 1.000 | yes | 0.21 |
| metal | metal | 1.000 | yes | 0.24 |
| paper | paper | 0.925 | yes | 0.22 |
| plastic | plastic | 0.480 | yes | 0.21 |
| shoes | shoes | 0.987 | yes | 0.19 |
| trash | trash | 0.999 | yes | 0.22 |

Live accuracy: **10 / 10**. Median response time **0.22 s** once the model is loaded. **Result: PASS.**

- **Date/time:** Part B run 2026-10-10 22:59 SGT (14:59 UTC). Part A from the notebook run before deployment.
- **Artefact path:** `evidence/raw/test3-live-output.txt`, `analytics/results/metrics.json`, `analytics/results/confusion_matrix_resnet50.png`
- **Interpretation:** The deployed model classifies 95% of unseen test images correctly, about 6 times better than the baseline, and the cloud service returns the same quality of answers in about 0.2 seconds. The weakest classes are trash (smallest class, 69 test images) and metal/paper, which are confused with visually similar materials.

## Limitations

- **Same-source test images.** The test images come from the same dataset as the training images (clean, centred, often studio-style photos). Real campus photos with clutter, poor lighting or several items may score lower. The 10/10 live result is a small sample from the same distribution, so it confirms the deployment works but does not prove real-world accuracy.
- **Low-confidence correct answers.** The plastic image was correct with only 48% confidence. The app currently shows the top answer regardless of confidence. Improvement: below about 60%, show "Not sure, please check the bin label" instead of awarding full points.
- **Class imbalance.** Clothes has 1,892 images and trash 453 (4.2x). Class weights were used in training, but trash still has the lowest F1 (0.87).
- **Cold start.** The first scan on a new server took 10.8 s because the 225 MB model loads on first use. Improvement: load the model at service start-up so the ALB only routes traffic once it is ready.
- **Single label.** One photo gets one class; mixed items (e.g. a coffee cup with a plastic lid) cannot be represented.

## Responsible use

- Uploaded images are not stored; only the filename and the prediction are saved in `scan_logs`.
- All test users are synthetic (`@example.com`); no personal data was used.
- Bin advice follows Singapore NEA blue-bin guidance; batteries, clothes and shoes are routed to special collection points rather than the blue bin.
- Predictions are guidance, not a guarantee: the app should never penalise a user for a model mistake.
