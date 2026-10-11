# Dataset

## Source and licence

- **Dataset:** Garbage Classification V2 by sumn2u on Kaggle: https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2 (the `original` image folder).
- **Licence:** MIT, as listed on the Kaggle dataset page.
- **Content:** public photos of waste items in 10 classes (battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoes, trash). No personal or student data.

## How it was used

- 12,259 labelled images were used, split 70 / 15 / 15 with random seed 42: train 8,578, validation 1,833, test 1,848. The split and training are in `analytics/cloudmodel.ipynb`.
- Class balance: `analytics/results/class_distribution.png`.

## What is in this folder

| Path | Contents |
| --- | --- |
| `testing_images/` | The held-out **test split** (1,848 images, one subfolder per class), so the evaluation can be re-run. Training and validation images are not included because of size; download them from the Kaggle link above. |
| `DATA_DICTIONARY.md` | The image dataset used to train and test the classifier: source, label, and the train/validation/test split. |
| `sample_scans.csv` | Synthetic example scan records (not real users), used only by `analytics/train_baseline.py`. |

Images uploaded by app users are not stored in this repository.
