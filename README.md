# AI Revenue Copilot (MVP)

A local Python MVP for a small-business "Revenue Copilot" that:
- stores incoming leads,
- scores lead heat,
- suggests follow-up messages,
- tracks follow-up actions.

## Quick start

```bash
python -m unittest -v
```

## Service methods (`RevenueCopilotService`)

- `create_lead(...)`
- `list_leads(status=None)`
- `score_lead(lead_id)`
- `followup_lead(lead_id)`
- `add_event(lead_id, event)`
- `health()`

## Notes

This is intentionally lightweight and local-file backed (`data/leads.json`) so it's easy to iterate quickly before adding APIs/integrations.


## KNN evaluation snippet (no extra installs)

If you want a KNN example that does not depend on external ML packages, use this pure-Python snippet:

```python
import math
from collections import Counter

def minkowski_distance(a, b, p=2):
    return sum(abs(x - y) ** p for x, y in zip(a, b)) ** (1 / p)

def knn_predict(X_train, y_train, X_test, k=11, p=1):
    preds = []
    for x in X_test:
        distances = [(minkowski_distance(x, x_train, p), y) for x_train, y in zip(X_train, y_train)]
        distances.sort(key=lambda t: t[0])
        top_k = [label for _, label in distances[:k]]
        preds.append(Counter(top_k).most_common(1)[0][0])
    return preds

def confusion_matrix_binary(y_true, y_pred, pos_label=1):
    tp = tn = fp = fn = 0
    for yt, yp in zip(y_true, y_pred):
        if yt == pos_label and yp == pos_label:
            tp += 1
        elif yt != pos_label and yp != pos_label:
            tn += 1
        elif yt != pos_label and yp == pos_label:
            fp += 1
        else:
            fn += 1
    return [[tn, fp], [fn, tp]]

def accuracy_score(y_true, y_pred):
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true)

def precision_recall_f1(y_true, y_pred, pos_label=1):
    cm = confusion_matrix_binary(y_true, y_pred, pos_label)
    tn, fp = cm[0]
    fn, tp = cm[1]
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1

# X_train, X_test, y_train, y_test should already be prepared in your script.
y_pred_knn = knn_predict(X_train, y_train, X_test, k=11, p=1)
cm = confusion_matrix_binary(y_test, y_pred_knn, pos_label=1)
acc = accuracy_score(y_test, y_pred_knn)
prec, rec, f1 = precision_recall_f1(y_test, y_pred_knn, pos_label=1)

print("KNN")
print("Confusion Matrix:")
print(cm)
print("Accuracy:", acc)
print("Precision:", prec)
print("Recall:", rec)
print("F1:", f1)
```
