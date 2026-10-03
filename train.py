"""Run: python train.py. Rebuilds data, frozen split, model and evaluation."""

import os

# Avoid thread overhead on these small matrices; set before importing NumPy.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np

from beamnet.network import Network, fit, predict_artifact
from beamnet.physics import FEATURES, HIGH, LOW, OUTPUTS, generate_data

ROOT = Path(__file__).resolve().parent


def metrics(y, pred):
    result = {}
    for i, name in enumerate(OUTPUTS):
        error = pred[:, i] - y[:, i]
        relative = np.abs(error / y[:, i]) * 100
        result[name] = {"mae": float(np.mean(np.abs(error))),
                        "rmse": float(np.sqrt(np.mean(error**2))),
                        "mape_pct": float(np.mean(relative)),
                        "p95_ape_pct": float(np.percentile(relative, 95)),
                        "max_ape_pct": float(np.max(relative)),
                        "r2": float(1 - np.sum(error**2) / np.sum((y[:, i] - y[:, i].mean())**2))}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=500)
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("--epochs must be positive")
    for folder in ("data", "artifacts", "web", "reports"):
        (ROOT / folder).mkdir(exist_ok=True)
    started = time.perf_counter()
    x, y = generate_data()
    order = np.random.default_rng(2026).permutation(len(x))
    tr, va, te = order[:6000], order[6000:8000], order[8000:]
    np.savez_compressed(ROOT / "data/dataset.npz", x=x, y=y, train=tr, validation=va, test=te)
    xm, xs = x[tr].mean(axis=0), x[tr].std(axis=0)
    ym, ys = np.log(y[tr]).mean(axis=0), np.log(y[tr]).std(axis=0)
    xn, yn = (x - xm) / xs, (np.log(y) - ym) / ys
    model = Network()
    history, epoch = fit(model, xn[tr], yn[tr], xn[va], yn[va], epochs=args.epochs)
    artifact = {"schema_version": 1, "architecture": [5, 64, 64, 2],
                "activation": "tanh", "output_transform": "exp",
                "features": FEATURES, "outputs": OUTPUTS, "low": LOW.tolist(), "high": HIGH.tolist(),
                "x_mean": xm.tolist(), "x_scale": xs.tolist(),
                "y_mean": ym.tolist(), "y_scale": ys.tolist(), **model.to_dict()}
    # Baseline: least-squares linear model on standardized physical inputs,
    # with identical standardized log targets. No hyperparameters selected on test.
    design = np.column_stack((xn[tr], np.ones(len(tr))))
    coefficients = np.linalg.lstsq(design, yn[tr], rcond=None)[0]
    baseline = np.exp((np.column_stack((xn[te], np.ones(len(te)))) @ coefficients) * ys + ym)
    pred = predict_artifact(artifact, x[te])  # first test evaluation, after selection
    errors = np.abs(pred / y[te] - 1).max(axis=1)
    worst = np.argsort(errors)[-5:][::-1]
    report = {"project": "BeamLab", "data_source": "Synthetic Euler-Bernoulli equations; no ANSYS training data",
              "n_samples": len(x), "split": {"train": len(tr), "validation": len(va), "test": len(te)},
              "seeds": {"data": 42, "split": 2026, "weights": 7, "minibatch": 19},
              "architecture": artifact["architecture"], "parameters": sum(w.size + b.size for w, b in zip(model.weights, model.biases)),
              "selected_epoch": epoch, "epochs_run": history[-1]["epoch"], "history": history,
              "selection": "Lowest validation MSE in standardized log targets; checkpoint every 5 epochs",
              "neural_network": metrics(y[te], pred), "linear_baseline": metrics(y[te], baseline),
              "equation_reference_error_pct": 0.0,
              "equation_reference_note": "Zero by construction: the reference equations generated all labels. They remain preferable for this simple beam.",
              "training_seconds": time.perf_counter() - started,
              "environment": {"python": platform.python_version(), "numpy": np.__version__},
              "dataset_sha256": hashlib.sha256(x.tobytes() + y.tobytes()).hexdigest(),
              "test_rows": te.tolist(),
              "worst_cases": [{"row": int(te[i]), "x": x[te[i]].tolist(), "reference": y[te[i]].tolist(),
                               "prediction": pred[i].tolist(), "max_ape_pct": float(errors[i] * 100)} for i in worst],
              "parity_samples": [{"x": x[te[i]].tolist(), "y": pred[i].tolist()} for i in range(32)],
              "scatter": [{"reference": y[te[i]].tolist(), "prediction": pred[i].tolist()} for i in range(0, len(te), 10)]}
    slices = {}
    for label, mask in {"slenderness_10_to_15": x[te, 0] / x[te, 2] < 15,
                        "slenderness_15_plus": x[te, 0] / x[te, 2] >= 15,
                        "stress_above_100_mpa": y[te, 1] > 100}.items():
        slices[label] = {"n": int(mask.sum()), "metrics": metrics(y[te][mask], pred[mask])}
    report["slices"] = slices
    (ROOT / "artifacts/model.json").write_text(json.dumps(artifact, separators=(",", ":")), encoding="utf-8")
    (ROOT / "reports/metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (ROOT / "web/model-data.js").write_text("globalThis.BEAM_MODEL=" + json.dumps(artifact, separators=(",", ":")) + ";\n", encoding="utf-8")
    (ROOT / "web/report-data.js").write_text("globalThis.BEAM_REPORT=" + json.dumps(report, separators=(",", ":")) + ";\n", encoding="utf-8")
    with (ROOT / "reports/test_predictions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["dataset_row", *FEATURES, "reference_deflection_mm", "reference_stress_mpa", "predicted_deflection_mm", "predicted_stress_mpa"])
        writer.writerows([int(row), *x[row], *y[row], *p] for row, p in zip(te, pred))
    print(json.dumps({"selected_epoch": epoch, "seconds": report["training_seconds"], "neural_network": report["neural_network"], "linear_baseline": report["linear_baseline"]}, indent=2))


if __name__ == "__main__":
    main()
