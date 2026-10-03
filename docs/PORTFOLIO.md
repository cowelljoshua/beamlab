# Presenting BeamLab to mechanical-engineering recruiters

## Your project story

“I wanted to understand how a neural-network surrogate could fit into an
engineering analysis workflow. I used a cantilever with known answers, built
a reproducible training pipeline, checked held-out errors, cross-checked six
cases in ANSYS and deployed the trained weights in an interactive browser demo.”

Use this account only once you have personally reproduced the workflow and
can explain it. The initial implementation was made with AI assistance. Say so
if asked about your development process. Do not claim independent authorship
of every line, production use, GLE endorsement or proprietary company data.

## Resume bullet after you can explain and reproduce the project

**BeamLab — Neural-Network Surrogate for Beam Response | Python, NumPy, ANSYS, JavaScript**

- Developed and evaluated a 4,674-parameter neural-network surrogate using
  10,000 synthetic beam cases; achieved 0.57% mean deflection error and 0.40%
  mean bending-stress error on 2,000 held-out cases; cross-checked six designs
  with 18 ANSYS solves and deployed an interactive browser demo.

If you are still learning it, use “Built an AI-assisted engineering prototype”
instead of implying mastery. Avoid “99.6% accurate,” “validated for real-world
design,” “ANSYS-trained,” “replaced FEA” or an unmeasured speedup claim.

## A 90-second live or recorded demo

| Time | What to show | What to say |
|---|---|---|
| 0–15 sec | Default beam | Five design inputs feed a trained network; two outputs describe elastic response. |
| 15–35 sec | Increase height | Geometry has a nonlinear effect. Compare the network with the known equation. |
| 35–50 sec | Model validation | Keep training, validation and test separate; show mean and worst-case errors. |
| 50–65 sec | ANSYS table | Six designs, three meshes each; explain why shear creates a small difference. |
| 65–80 sec | Short, thick beam | Out-of-domain inputs are rejected. A model should know where its evidence stops. |
| 80–90 sec | Return to default | This is a learning surrogate; equations are best here, while the workflow transfers to expensive simulations. |

Record at about 1440×1000 or use browser zoom to keep results visible. Hide
unrelated browser tabs and record only the app. OBS, Windows screen capture or
your usual recorder will work; the project itself needs no video service.

## Questions you should be ready to answer

1. **Why a neural network?** To demonstrate and inspect a surrogate workflow,
   not because a neural network is the best solver for this beam.
2. **Where did data come from?** Euler–Bernoulli equations with explicit units
   and filters, not ANSYS or experimental measurements.
3. **What is backpropagation?** Applying the chain rule to calculate loss
   gradients with respect to weights and biases.
4. **How did you prevent leakage?** Disjoint seeded splits, training-only
   scalers, validation-selected checkpoint, final test evaluation afterward.
5. **What are limitations?** Synthetic distribution, a narrow beam model,
   no yield/fatigue/buckling/joint effects, no certified design decisions.
6. **What did ANSYS add?** Independent numerical spot checks, mesh consistency,
   reaction-force balance and a chance to explain shear-model differences.
7. **What would you do next?** Train on a verified parametric FEA study; use
   held-out geometry families, investigate uncertainty and verify with tests.

## A useful next contribution

Choose one change you can own and explain: compare a smaller network using
validation data, measure inference times against equations without assuming a
speedup, or automate a new beam load case in ANSYS. Record the hypothesis,
method, result and limitation in a short experiment note. Keep final evaluation
independent of decisions made while inspecting results.

For GLE applications, connect the project to mechanics, careful verification
and engineering automation. Do not invent a connection to confidential
equipment, processes or company-specific requirements.
