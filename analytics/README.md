# Analytics — ResNet50 model and evaluation

The production classifier is the trained ResNet50 model at `src/app/ml/artefacts/resnet50_final.keras`. The API uses it for inference and maps its ten output indices to the class order in `src/app/ml/service.py`:
`battery, biological, cardboard, clothes, glass, metal, paper, plastic, shoes, trash` (alphabetical, matching the training generator).

Input images are resized to 224×224 and preprocessed with ResNet50's `preprocess_input`, the same as during training.

## Training and dataset

- Notebook: `cloudmodel.ipynb` (data checks, training, model comparison, evaluation)
- Dataset: Garbage Classification V2, Kaggle (sumn2u/garbage-classification-v2), 12,259 images, 10 classes
- Split: 70/15/15 train/val/test with seed 42 (8,578 / 1,833 / 1,848 images)
- Method: ImageNet-pretrained ResNet50, two-phase transfer learning (frozen base, then fine-tuning the top 30% of layers), with augmentation and balanced class weights
- EfficientNetB0 was trained the same way for comparison

## Results (held-out test set, 1,848 images)

| Model | Test accuracy | Macro F1 |
|---|---|---|
| ResNet50 (deployed) | 94.86% | 94.28% |
| EfficientNetB0 | 93.29% | 92.65% |

The weakest classes are trash (F1 0.87), metal (0.90) and paper (0.90). The most common mix-ups are cardboard→paper and plastic↔glass. See `confusion_matrix_ResNet50.png`.

## Re-run the evaluation

Pass a labelled image folder whose subfolders are the ten class names. Use only held-out images; the script does not create a split.

```bash
python analytics/evaluate_model.py --dataset dataImages/split/test
```

This writes accuracy and per-class precision, recall, F1 and support to `analytics/results/metrics.json`, and a confusion matrix to `analytics/results/confusion_matrix.png`.
