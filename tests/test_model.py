import json
import unittest
from pathlib import Path

import numpy as np

from beamnet.network import Network, predict_artifact
from beamnet.physics import reference, valid_domain

ROOT = Path(__file__).resolve().parents[1]


class PhysicsTests(unittest.TestCase):
    def test_hand_calculated_case_and_units(self):
        # I = 30*25^3/12 = 39,062.5 mm^4; sigma = 16 MPa.
        np.testing.assert_allclose(reference([500, 30, 25, 69000, 100]), [1.5458937198067633, 16])

    def test_physical_scaling(self):
        x = np.array([500, 30, 25, 69000, 100.0])
        y = reference(x)
        double_load = x.copy(); double_load[4] *= 2
        double_height = x.copy(); double_height[2] *= 2
        np.testing.assert_allclose(reference(double_load), 2*y)
        np.testing.assert_allclose(reference(double_height), y / [8, 4])

    def test_invalid_inputs_and_domain(self):
        for x in ([0, 30, 25, 69000, 100], [500, 30, 25, np.nan, 100]):
            with self.assertRaises(ValueError): reference(x)
        self.assertFalse(valid_domain([200, 30, 60, 69000, 100]))
        self.assertFalse(valid_domain([1000, 15, 10, 69000, 500]))


class NetworkTests(unittest.TestCase):
    def test_backprop_against_finite_differences(self):
        rng = np.random.default_rng(9)
        model = Network((3, 4, 2))
        x, y = rng.normal(size=(5, 3)), rng.normal(size=(5, 2))
        _, dw, db = model.loss_gradients(x, y)
        for p, gradient in zip(model.weights + model.biases, dw + db):
            for index in np.ndindex(p.shape):
                original, eps = p[index], 1e-6
                p[index] = original + eps
                plus = np.mean((model.predict(x)-y)**2)
                p[index] = original - eps
                minus = np.mean((model.predict(x)-y)**2)
                p[index] = original
                self.assertAlmostEqual((plus-minus)/(2*eps), gradient[index], places=6)

    def test_round_trip(self):
        model = Network()
        x = np.random.default_rng(10).normal(size=(8,5))
        restored = Network.from_dict(json.loads(json.dumps(model.to_dict())))
        np.testing.assert_allclose(model.predict(x), restored.predict(x), atol=1e-12)

    def test_frozen_artifact_and_split_integrity(self):
        data = np.load(ROOT / "data/dataset.npz")
        sets = [set(data[k].tolist()) for k in ("train", "validation", "test")]
        self.assertEqual([len(s) for s in sets], [6000,2000,2000])
        self.assertFalse(sets[0] & sets[1] or sets[1] & sets[2] or sets[0] & sets[2])
        self.assertEqual(len(set.union(*sets)), 10000)
        self.assertEqual(len(np.unique(data["x"],axis=0)), 10000)
        self.assertTrue(np.all(valid_domain(data["x"])))
        model = json.loads((ROOT / "artifacts/model.json").read_text())
        np.testing.assert_allclose(model["x_mean"], data["x"][data["train"]].mean(axis=0))
        np.testing.assert_allclose(model["y_mean"], np.log(data["y"][data["train"]]).mean(axis=0))
        report = json.loads((ROOT / "reports/metrics.json").read_text())
        self.assertEqual(report["test_rows"], data["test"].tolist())
        pred = predict_artifact(model, data["x"][data["test"]])
        errors = np.abs(pred / data["y"][data["test"]] - 1).mean(axis=0)*100
        for i, name in enumerate(model["outputs"]):
            self.assertAlmostEqual(errors[i], report["neural_network"][name]["mape_pct"], places=10)


if __name__ == "__main__":
    unittest.main()
