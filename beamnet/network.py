"""A fully connected regressor. NumPy supplies arrays, not a neural-net API.

The forward pass, chain-rule gradients and Adam update are written explicitly.
"""

import numpy as np


class Network:
    def __init__(self, sizes=(5, 64, 64, 2), seed=7):
        rng = np.random.default_rng(seed)
        self.weights = [rng.normal(0, np.sqrt(2 / (a + b)), (a, b))
                        for a, b in zip(sizes[:-1], sizes[1:])]
        self.biases = [np.zeros(b) for b in sizes[1:]]

    def forward(self, x):
        activations = [np.asarray(x)]
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = activations[-1] @ w + b
            activations.append(np.tanh(z) if i < len(self.weights) - 1 else z)
        return activations

    def predict(self, x):
        return self.forward(x)[-1]

    def loss_gradients(self, x, y):
        a = self.forward(x)
        residual = a[-1] - y
        loss = np.mean(residual**2)
        delta = 2 * residual / residual.size
        dw, db = [None] * len(self.weights), [None] * len(self.biases)
        for i in reversed(range(len(self.weights))):
            dw[i], db[i] = a[i].T @ delta, delta.sum(axis=0)
            if i:
                delta = (delta @ self.weights[i].T) * (1 - a[i]**2)
        return float(loss), dw, db

    def to_dict(self):
        return {"weights": [w.tolist() for w in self.weights],
                "biases": [b.tolist() for b in self.biases]}

    @classmethod
    def from_dict(cls, data):
        model = cls()
        model.weights = [np.asarray(w, dtype=float) for w in data["weights"]]
        model.biases = [np.asarray(b, dtype=float) for b in data["biases"]]
        return model


def fit(model, x, y, xv, yv, epochs=500, batch_size=256, seed=19):
    """Select checkpoint only by validation loss; the test set is not accepted."""
    params = model.weights + model.biases
    m, v = [np.zeros_like(p) for p in params], [np.zeros_like(p) for p in params]
    rng, step = np.random.default_rng(seed), 0
    best, best_epoch, best_weights, stale = np.inf, 0, None, 0
    history = []
    for epoch in range(1, epochs + 1):
        order = rng.permutation(len(x))
        learning_rate = 0.002 * (0.4 ** ((epoch - 1) // 150))
        for start in range(0, len(x), batch_size):
            batch = order[start:start + batch_size]
            _, dw, db = model.loss_gradients(x[batch], y[batch])
            step += 1
            for i, (p, g) in enumerate(zip(params, dw + db)):
                m[i] = 0.9 * m[i] + 0.1 * g
                v[i] = 0.999 * v[i] + 0.001 * g**2
                p -= learning_rate * (m[i] / (1 - 0.9**step)) / (
                    np.sqrt(v[i] / (1 - 0.999**step)) + 1e-8)
        if epoch == 1 or epoch % 5 == 0:
            training = float(np.mean((model.predict(x) - y)**2))
            validation = float(np.mean((model.predict(xv) - yv)**2))
            history.append({"epoch": epoch, "train_loss": training, "val_loss": validation})
            if validation < best - 1e-8:
                best, best_epoch, stale = validation, epoch, 0
                best_weights = [p.copy() for p in params]
            else:
                stale += 5
            if epoch % 50 == 0:
                print(f"Epoch {epoch:3d}: train={training:.6f}, validation={validation:.6f}", flush=True)
            if stale >= 60:
                break
    for p, checkpoint in zip(params, best_weights):
        p[:] = checkpoint
    return history, best_epoch


def predict_artifact(artifact, x):
    x = np.asarray(x, dtype=float)
    z = (x - artifact["x_mean"]) / artifact["x_scale"]
    log_y = Network.from_dict(artifact).predict(z) * artifact["y_scale"] + artifact["y_mean"]
    return np.exp(log_y)
