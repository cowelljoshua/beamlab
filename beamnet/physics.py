"""Units: mm, N, MPa (N/mm²). Elastic, prismatic, end-loaded cantilever."""

import numpy as np

FEATURES = ["length_mm", "width_mm", "height_mm", "modulus_mpa", "force_n"]
LOW = np.array([200.0, 15.0, 10.0, 69000.0, 10.0])
HIGH = np.array([1000.0, 60.0, 60.0, 210000.0, 500.0])
OUTPUTS = ["tip_deflection_mm", "root_bending_stress_mpa"]


def reference(x):
    """Return positive magnitudes. No self-weight, shear, plasticity or dynamics."""
    a = np.asarray(x, dtype=float)
    if a.shape[-1] != 5 or not np.isfinite(a).all() or np.any(a <= 0):
        raise ValueError("Expected five finite, positive inputs: L, b, h, E, F.")
    length, width, height, modulus, force = np.moveaxis(a, -1, 0)
    inertia = width * height**3 / 12
    return np.stack((force * length**3 / (3 * modulus * inertia),
                     6 * force * length / (width * height**2)), axis=-1)


def valid_domain(x):
    """Training envelope; these limits are not a design acceptance criterion."""
    x = np.asarray(x, dtype=float)
    y = reference(x)
    return ((x >= LOW).all(axis=-1) & (x <= HIGH).all(axis=-1)
            & (x[..., 0] / x[..., 2] >= 10)
            & (y[..., 0] / x[..., 0] <= 0.02)
            & (y[..., 1] <= 200))


def generate_data(n=10000, seed=42):
    """Rejection-sampled synthetic data, uniform in the five physical inputs."""
    rng = np.random.default_rng(seed)
    chunks, count = [], 0
    while count < n:
        candidates = rng.uniform(LOW, HIGH, size=(n, 5))
        accepted = candidates[valid_domain(candidates)]
        chunks.append(accepted)
        count += len(accepted)
    x = np.concatenate(chunks)[:n]
    return x, reference(x)
