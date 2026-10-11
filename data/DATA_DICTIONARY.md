# Data dictionary

This file describes the images used to train and test the classifier. It does not describe the web app database. Accounts and scan logs live in the `users` and `scan_logs` tables.

## Dataset

| Item | Value |
| --- | --- |
| Name | Garbage Classification V2, `original` folder, by sumn2u on Kaggle |
| Source | https://www.kaggle.com/datasets/sumn2u/garbage-classification-v2 |
| Licence | MIT, as listed on the Kaggle page |
| Images | 12,259 labelled photos of waste items. No student or personal data |
| Split | 70% train / 15% validation / 15% test, random seed 42 |
| Counts | Train 8,578, validation 1,833, test 1,848 |
| Where the split is defined | `analytics/cloudmodel.ipynb` |

Training and validation images are not in this repository because of size. Download them from the Kaggle link. The held-out test split is in `data/testing_images/`.

## What one example is

Each example is one image file. The class label is the name of the folder the file sits in, not a column in a table.

| Item | Meaning |
| --- | --- |
| File | A `.jpg` photo, for example `data/testing_images/metal/metal_139.jpg` |
| Label | The folder name. One of `battery`, `biological`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`, `shoes`, `trash` |
| Used for | Supervised training of ResNet50. At inference the same folders tell the evaluation script the correct class |

`analytics/evaluate_model.py` reads a folder laid out this way, resizes each image to 224×224, and scores the deployed model.

## Test images kept in the repo

`data/testing_images/` has the 1,848 test images, one subfolder per class. These images were not used for training.

| Class | Test images |
| --- | --- |
| battery | 114 |
| biological | 106 |
| cardboard | 213 |
| clothes | 285 |
| glass | 261 |
| metal | 140 |
| paper | 201 |
| plastic | 241 |
| shoes | 218 |
| trash | 69 |

## Not the training set

`data/sample_scans.csv` is a small synthetic file for the majority-class baseline in `analytics/train_baseline.py`. It is not the Kaggle image set.
