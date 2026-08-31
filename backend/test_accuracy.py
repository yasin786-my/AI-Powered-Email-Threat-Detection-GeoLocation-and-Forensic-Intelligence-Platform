"""
Evaluate XGBoost fraud model accuracy on the 6 seed .eml files.

Ground-truth labels live in seed_data/labels.json:
  0 = legitimate, 1 = phishing/fraud

Usage:
    python test_accuracy.py
    python test_accuracy.py --threshold 40
    python test_accuracy.py --verbose
"""

import argparse
import glob
import json
import os
import sys

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

from geo_intel import trace_origin
from ml_model import (
    FEATURE_COLUMNS,
    build_feature_vector,
    get_risk_tier,
    predict_fraud,
    _load_model,
)
from parser import parse_eml

SEED_DIR = os.path.join(os.path.dirname(__file__), "seed_data")
LABELS_PATH = os.path.join(SEED_DIR, "labels.json")


def load_labels():
    with open(LABELS_PATH, encoding="utf-8") as f:
        return json.load(f)


def evaluate_eml(eml_path, label_meta):
    filename = os.path.basename(eml_path)
    with open(eml_path, "rb") as f:
        header_data = parse_eml(f.read())

    geo_data = trace_origin(
        header_data.get("relay_hops", []),
        from_domain=header_data.get("from_domain"),
    )
    features = build_feature_vector(header_data, geo_data)
    score, flags, contributions = predict_fraud(features)

    # Evaluate the production decision path (calibrated score), not XGBoost's
    # synthetic-data class output.
    pred_label = int(score >= 50)

    return {
        "file": filename,
        "subject": header_data.get("subject", ""),
        "true_label": label_meta["label"],
        "true_type": label_meta["type"],
        "description": label_meta.get("description", ""),
        "pred_label": pred_label,
        "fraud_score": score,
        "risk_tier": get_risk_tier(score),
        "fraud_probability": round(score / 100, 4),
        "flags": flags,
        "contributions": contributions,
        "features": features,
    }


def score_to_label(fraud_score, threshold):
    return 1 if fraud_score >= threshold else 0


def main():
    parser = argparse.ArgumentParser(
        description="Test ML accuracy on 6 seed .eml files"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=50,
        help="Fraud score threshold for binary prediction (default: 50)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print feature vectors for each email",
    )
    args = parser.parse_args()

    if not os.path.exists(LABELS_PATH):
        print(f"[ERROR] Missing labels file: {LABELS_PATH}")
        sys.exit(1)

    labels = load_labels()
    eml_files = sorted(glob.glob(os.path.join(SEED_DIR, "email_*.eml")))

    if len(eml_files) != 6:
        print(f"[WARN] Expected 6 .eml files, found {len(eml_files)}")

    results = []
    for eml_path in eml_files:
        filename = os.path.basename(eml_path)
        if filename not in labels:
            print(f"[SKIP] No label for {filename}")
            continue
        results.append(evaluate_eml(eml_path, labels[filename]))

    if not results:
        print("[ERROR] No labeled .eml files to evaluate.")
        sys.exit(1)

    y_true = [r["true_label"] for r in results]
    y_pred_model = [r["pred_label"] for r in results]
    y_pred_score = [score_to_label(r["fraud_score"], args.threshold) for r in results]

    model_acc = accuracy_score(y_true, y_pred_model)
    score_acc = accuracy_score(y_true, y_pred_score)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred_model, average="binary", zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred_model, labels=[0, 1])

    print("\n" + "=" * 72)
    print("  CYBERFORENSIX — ML ACCURACY TEST (6 seed .eml files)")
    print("=" * 72)
    print(f"  Model file     : fraud_model.json")
    print(f"  Score threshold: {args.threshold}/100")
    print(f"  Test set       : {len(results)} emails "
          f"({sum(1 for y in y_true if y == 1)} phishing, "
          f"{sum(1 for y in y_true if y == 0)} legitimate)")
    print("=" * 72)

    print("\nPer-email results:\n")
    print(f"{'File':<16} {'True':<12} {'Pred':<12} {'Score':<8} {'Tier':<10} {'Result'}")
    print("-" * 72)

    for r in results:
        correct = r["pred_label"] == r["true_label"]
        status = "CORRECT" if correct else "WRONG"
        print(
            f"{r['file']:<16} {r['true_type']:<12} "
            f"{'phishing' if r['pred_label'] else 'legitimate':<12} "
            f"{r['fraud_score']:<8} {r['risk_tier']:<10} {status}"
        )
        print(f"  Subject: {r['subject'][:65]}")
        if r["flags"]:
            print(f"  Flags  : {', '.join(r['flags'][:4])}")
        if args.verbose:
            print("  Features:")
            for key in FEATURE_COLUMNS:
                print(f"    {key:28s} {r['features'][key]}")
        print()

    print("-" * 72)
    print(f"  Calibrated decision accuracy: {model_acc:.1%}  ({sum(a == b for a, b in zip(y_true, y_pred_model))}/{len(results)})")
    print(f"  Score >= {args.threshold} accuracy      : {score_acc:.1%}  ({sum(a == b for a, b in zip(y_true, y_pred_score))}/{len(results)})")
    print(f"  Precision (phishing)       : {precision:.1%}")
    print(f"  Recall (phishing)          : {recall:.1%}")
    print(f"  F1 (phishing)              : {f1:.3f}")
    print("\n  Confusion matrix (rows=actual, cols=predicted):")
    print("                 Legit  Phish")
    print(f"  Actual Legit     {cm[0][0]:3d}    {cm[0][1]:3d}")
    print(f"  Actual Phish     {cm[1][0]:3d}    {cm[1][1]:3d}")
    print("\n  Classification report:")
    print(classification_report(
        y_true,
        y_pred_model,
        target_names=["Legitimate", "Phishing"],
        zero_division=0,
    ))
    print("=" * 72)

    return 0 if model_acc == 1.0 else 1


if __name__ == "__main__":
    sys.exit(main())
