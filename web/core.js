/* Shared by the browser and Node verification. No inference service needed. */
(function (root) {
  "use strict";
  function reference(x) {
    if (x.length !== 5 || x.some(v => !Number.isFinite(v) || v <= 0)) throw new Error("Enter five positive, finite inputs.");
    const [L, b, h, E, F] = x;
    return [4 * F * L ** 3 / (E * b * h ** 3), 6 * F * L / (b * h ** 2)];
  }
  function domain(x, model) {
    if (x.length !== 5 || x.some(v => !Number.isFinite(v))) return "Enter a number in every field.";
    for (let i = 0; i < 5; i++) {
      if (x[i] < model.low[i] || x[i] > model.high[i]) return "An input is outside its training range. Use the limits shown below each field.";
    }
    if (x[0] / x[2] < 10) return "This beam is too short relative to its height: L/h must be at least 10. Increase length or reduce height.";
    const y = reference(x);
    if (y[0] / x[0] > 0.02) return "Deflection exceeds 2% of length, outside the training envelope. Reduce load or increase section height.";
    if (y[1] > 200) return "Reference bending stress exceeds the 200 MPa training limit. Reduce load or increase the section.";
    return null;
  }
  function predict(x, model) {
    const problem = domain(x, model);
    if (problem) throw new Error(problem);
    let a = x.map((v, i) => (v - model.x_mean[i]) / model.x_scale[i]);
    const activations = [a];
    model.weights.forEach((w, layer) => {
      a = model.biases[layer].map((b, j) => {
        const value = a.reduce((sum, v, i) => sum + v * w[i][j], b);
        return layer < model.weights.length - 1 ? Math.tanh(value) : value;
      });
      activations.push(a);
    });
    return { values: a.map((v, i) => Math.exp(v * model.y_scale[i] + model.y_mean[i])), activations };
  }
  root.BeamCore = { reference, domain, predict };
  if (typeof module !== "undefined") module.exports = root.BeamCore;
})(globalThis);
