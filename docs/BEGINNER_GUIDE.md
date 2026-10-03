# Neural networks, explained through your BeamLab project

This guide starts with something familiar to a mechanical engineer: a beam.
You can read it alongside the working demo. You do not need prior AI experience.

## 1. What you have built

BeamLab takes five numbers: beam length L, rectangular-section width b, height h,
Young's modulus E, and a downward force F at the free end. It predicts two things:
how far the free end moves and the maximum bending-stress magnitude at the root.

The beam is clamped perfectly at one end. Its section is constant. Everything
is linearly elastic and static, with small deflections. The model ignores
self-weight. Those assumptions define the problem; they are not minor details.

The browser contains the actual trained network. Moving a slider runs matrix
multiplications through its saved weights. It also calculates an independent
equation reference so you can compare the two answers immediately.

**Try it:** open `index.html`. The initial beam is 500 mm long, 30 mm wide and
25 mm tall, with E = 69 GPa and F = 100 N. Its equation-reference response is
1.545894 mm deflection and 16 MPa bending stress. The neural results are close,
but do not have to equal these numbers.

## 2. A network is an adjustable mathematical function

A conventional beam formula is fixed:

```text
I = b h³ / 12             second moment of area, mm⁴
δ = F L³ / (3 E I)        free-end deflection magnitude, mm
σ = 6 F L / (b h²)        root bending stress magnitude, MPa
```

Here we use mm, N and MPa together. Since 1 MPa = 1 N/mm², the units are
consistent. The interface converts E from GPa to MPa before calculating.

A neural network starts with a flexible function containing thousands of
adjustable constants. Training finds constants that make its answers match
examples. The constants are called **parameters**: weights and biases.

Think of fitting a line y = mx + c to measurements. You adjust m and c until
the line fits. A neural network is a larger, nonlinear version of function
fitting. It does not automatically understand physical laws or causality.

## 3. What is a neuron?

A neuron takes inputs, multiplies each by a weight, adds the results and a bias,
and then applies an activation function:

```text
z = w₁x₁ + w₂x₂ + ... + bias
activation = tanh(z)
```

A weight changes the influence of one input. The bias shifts the result. The
tanh function bends a straight-line calculation into a nonlinear one, smoothly
mapping values between -1 and 1. Without nonlinear hidden activations, several
stacked linear layers would still represent only one linear function.

Our architecture is **5 → 64 → 64 → 2**:

- Five inputs describe the beam and load.
- Two hidden layers contain 64 neurons each.
- Two output neurons produce transformed deflection and stress.

The parameter count is (5×64+64) + (64×64+64) + (64×2+2) = **4,674**.
Hidden neurons need not correspond to physical features such as moment or
stiffness. Giving each neuron a physical interpretation would be unjustified.

## 4. Where the training examples come from

We generate 10,000 input combinations and calculate their known responses with
the equations above. This is **synthetic data**: generated mathematical answers,
not measurements and not ANSYS simulation output.

Candidates are sampled uniformly over each input range, then rejected if they
violate the domain filters. Consequently the accepted dataset is not uniform
over every individual input. The limits are:

| Quantity | Range |
|---|---|
| Length | 200–1,000 mm |
| Width | 15–60 mm |
| Height | 10–60 mm |
| Young's modulus | 69–210 GPa |
| Tip force | 10–500 N |

We also require L/h ≥ 10, reference δ/L ≤ 0.02, and reference σ ≤ 200 MPa.
These are the training envelope, not a promise that every beam in it is safe.
For example, the dataset does not specify yield strength.

The equations are intentionally simple. They let you learn and audit the AI
workflow before using expensive simulation data. A later project could train
on a carefully designed FEA study of a bracket, thermal component or joint.

## 5. How training works

First, each input is standardized: subtract its training-set mean and divide
by its training-set standard deviation. Otherwise E, around 69,000–210,000 MPa,
has a very different numerical scale from a width around 30 mm.

We take the natural logarithm of each positive target and standardize that too.
Learning in log space makes multiplicative differences easier to handle across
responses of different magnitudes. After prediction, the transformation is
reversed with an exponential, yielding positive physical outputs. Log-space
mean squared error is related to relative errors for small deviations; it is
not identical to the percentage-error metric shown in the demo.

The training loop repeats four steps:

1. **Forward pass:** run a batch of 256 cases through the current weights.
2. **Loss:** calculate mean squared error in standardized log-target space.
3. **Backpropagation:** use the calculus chain rule to calculate how each
   parameter changes the loss. These sensitivities are called gradients.
4. **Optimizer:** Adam uses moving averages of gradients and their squares to
   update the parameters. The learning rate controls the update scale.

One pass through the training set is an **epoch**. This run used 500 epochs.
Initialization and shuffled batches use fixed random seeds. We check validation
loss every five epochs and save the best checkpoint. The chosen checkpoint was
epoch 500. Early stopping is implemented, but did not stop this particular run.

The math is implemented in `beamnet/network.py`. NumPy provides array operations;
it does not train a ready-made neural-network object for us.

## 6. Why there are three datasets

The **6,000 training cases** update weights. The **2,000 validation cases**
select the checkpoint. The **2,000 test cases** measure final performance after
selection. Preprocessing statistics come from training cases only.

The test set is like an exam you do not study from. If you repeatedly adjust
the network after inspecting test results, the test set starts influencing the
design. It is no longer a clean final exam. For further development, reserve a
new independent final evaluation set and use validation for decisions.

**Overfitting** means learning details of the training cases that fail to
generalize. One sign is falling training loss while validation loss worsens.
Our curves let you inspect that relationship. Good curves on synthetic data
still do not prove accuracy on manufactured parts or a new kind of beam.

## 7. How to read the results honestly

For a single case, absolute percentage error is:

```text
100 × |prediction - reference| / |reference|
```

Targets here are strictly positive, so this denominator does not vanish.
On the frozen test set, the mean error was **0.57% for deflection** and
**0.40% for stress**. The 95th-percentile errors were 1.53% and 1.24%.
The worst observed errors were 10.49% and 10.07%.

These numbers mean different things. The mean summarizes typical error; the
95th percentile tells you how large errors were near the tail; the maximum
records the worst case in this sample. None guarantees an error bound on an
unseen case. R² measures fit relative to predicting the test-set mean; it is
not a probability, confidence score or percentage accuracy.

The baseline is a linear regression on the same physical inputs, with the same
log-target transformation. It has mean errors of 41.42% and 34.57%. The network
captures the nonlinear dependence much better than that particular baseline.
However, using logarithms of the inputs would make the known power laws linear.
That physics-informed baseline could reproduce the labels, as can the original
equations. Never claim the network is better than mechanics or all simpler models.

## 8. What ANSYS does and does not verify

We ran six separate beam cases with 4, 8 and 16 elements each: 18 linear static
MAPDL solves, using cubic BEAM188 elements. The clamped-end reaction balances
the applied force. Root bending stress is recovered from the element-end
bending moment and the section modulus, not a solid-element peak stress.

The largest ANSYS/equation deflection difference was 0.54%. A small difference
is expected: BEAM188 includes transverse shear, while our training equations
use Euler–Bernoulli bending theory. The neural network differed from ANSYS by
at most 1.48% in deflection and 1.21% in bending stress across these six designs.
The three mesh sizes also check numerical consistency. For a cubic beam under
this simple loading, very small mesh changes are expected; this is not a
general mesh-convergence study for complex 3D geometry.

These checks support numerical consistency under a narrow set of assumptions.
They do not validate the model against physical experiments, qualify a real
component, or make the network ANSYS-trained.

## 9. Training versus using the model

Training changes the weights and requires Python. **Inference** uses fixed
weights to predict a new case. The browser only performs inference. It does
not learn from your slider movements.

`artifacts/model.json` stores all weights, biases and scaling constants.
`web/core.js` reproduces the forward pass in JavaScript. A test compares 32
reference predictions between Python and JavaScript to within 1e-9 absolute
difference. This guards against deploying different math from what was trained.

Because inference is small and local, GitHub Pages can host the entire demo.
There is no backend and no Supabase dependency. Entered designs are not sent
to a server. The export button downloads a JSON case file to your device.

## 10. Three exercises before your interview

**Predict a physical trend.** Double height from 25 to 50 mm at the default
geometry. Equation deflection decreases by a factor of eight and stress by a
factor of four. Explain the h³ and h² terms, then check the neural approximation.

**Trigger a limit.** Set length to 200 mm and height to 60 mm. L/h is less than
10, so the demo withholds a neural result. Explain why predicting outside the
training envelope is different from interpolating within it.

**Inspect an error.** Open `reports/metrics.json` and find `worst_cases`. Compare
the inputs, prediction and reference. Explain why an average can hide a poor
individual result and what further validation you would want before design use.

Then run training yourself and read the gradient test. Change one experiment
at a time, write down your hypothesis, and record what changed. Keep the original
results so you can explain your contribution. The strongest resume story is
one you can reproduce, critique and extend.

## Further reading

- [Purdue mechanics-of-materials beam example](https://www.purdue.edu/freeform/me323/wp-content/uploads/sites/2/2018/10/ME323_F18_Hw7_final.pdf).
- [ANSYS BEAM188 reference](https://ansyshelp.ansys.com/public/views/secured/corp/v261/en/ans_elem/Hlp_E_BEAM188.html).
- [Adam: A Method for Stochastic Optimization](https://arxiv.org/abs/1412.6980).

The architecture, experimental setup and numbers in this guide come from the
local project and saved artifacts. This project was developed with AI assistance.
