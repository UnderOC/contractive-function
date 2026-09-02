### Kelly Criterion
```
// parameters: q in (0,1), b > 0, f in [0,1)

W := W0;
while true do
    if Bernoulli(q) then
        W := W * (1 + b * f)
    else
        W := W * (1 - f)
```


#### Kelly-related probabilistic program instances

The examples below are structurally close to contractive / multiplicative supermartingale arguments, and can all be expressed as probabilistic programs.

1. **Classical Bernoulli Kelly process**
   - Sampling statement: `Bernoulli(q)`
   - State: wealth `W`
   - Update: `W' = W * G`, where `G` is either `1 + b f` or `1 - f`
   - A natural multiplicative supermartingale candidate is $M_t = W_t^{-\lambda}$. The one-step condition becomes
$$
\mathbb{E}[M_{t+1} \mid \mathcal{F}_t] \le M_t
\iff
\mathbb{E}[G^{-\lambda}] \le 1 .
$$
   - Reference: Kelly, *A New Interpretation of Information Rate*. https://doi.org/10.1109/TIT.1956.1056803
   - This is the cleanest discrete example matching the template
$$
\mathbb{E}\left[e^{k \log (\eta'/\eta) + \ell} \mid \mathcal{F}_t\right] \le 1 .
$$

2. **Risk-constrained Kelly gambling**
   - Program schema:
```
W := W0
while true do
    sample r from ReturnDistribution
    choose b from Strategy
    W := W * <r, b>
```
   - Here `<r,b>` is the gross return factor in one round.
   - Taking $\eta(W) = W^{-\lambda}$ gives
$$
\frac{\eta'}{\eta} = (<r,b>)^{-\lambda},
$$
   so the prefixed-point / multiplicative supermartingale condition reduces to
$$
\mathbb{E}[(<r,b>)^{-\lambda} \mid \mathcal{F}_t] \le 1 .
$$
   - This is almost exactly the constraint used in risk-constrained Kelly gambling to derive drawdown bounds.
   - Reference: Busseti, Ryu, Boyd, *Risk-Constrained Kelly Gambling*. https://web.stanford.edu/~boyd/papers/kelly.html

3. **Bayesian Kelly criterion**
   - Program schema:
```
sample theta from Prior
W := W0
pi := PriorBelief
while true do
    sample y from ObservationModel(theta)
    pi := BayesianUpdate(pi, y)
    f := BetFraction(pi)
    W := W * G(y, f)
```
   - State: `(W, pi)` where `pi` is the posterior belief.
   - This yields a hidden-parameter probabilistic program. A more general candidate is
$$
\eta(W,\pi) = W^{-\lambda} h(\pi),
$$
   where `h` compensates for posterior drift.
   - Reference: Browne and Whitt, *Portfolio Choice and the Bayesian Kelly Criterion*. https://www.cambridge.org/core/journals/advances-in-applied-probability/article/portfolio-choice-and-the-bayesian-kelly-criterion/1B56265028071E0876F812C483B5B5ED

4. **Parameter uncertainty + particle filter Kelly trading**
   - Program schema:
```
sample theta from Prior
W := W0
particles := InitParticles(Prior)
while true do
    sample y from ObservationModel(theta)
    particles := ParticleFilterUpdate(particles, y)
    f := Policy(particles)
    W := W * G(y, f)
```
   - This is a state-space version of Kelly: the controller acts on an inferred latent state rather than a directly observed parameter.
   - Suitable for sequential Monte Carlo / probabilistic programming semantics.
   - Reference: Johnson, *Approximating Optimal Trading Strategies Under Parameter Uncertainty: A Monte Carlo Approach*. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1530754

5. **Regime-switching / hidden Markov Kelly model**
   - Program schema:
```
sample z from InitialRegime
W := W0
belief := InitialBelief
while true do
    sample z' from Transition(z)
    sample y from Emission(z')
    belief := FilterUpdate(belief, y)
    f := BetFraction(belief)
    W := W * G(y, f)
    z := z'
```
   - State: `(W, belief)` or `(W, z, belief)`.
   - The ratio $\eta'/\eta$ depends on both the return multiplier and the belief update. This is a natural continuous-state analogue of an eventually geometric distribution with hidden modes.
   - Reference: Dai, Zhang, Yang, Zhu, *Optimal Trend Following Trading Rules*. https://scholarworks.wmich.edu/math_pubs/44/

6. **Continuous multiplicative contraction example**
   - Program schema:
```
x := 10000
while (x >= 1) do
    sample r from Uniform(1/4, 3/2)
    x := x * r
```
   - Taking `\eta = x`, we have
$$
\mathbb{E}[\eta' \mid \eta] = \mathbb{E}[r] \eta = \frac{7}{8} \eta,
$$
   so `\eta` is contractive.
   - Your exponential-template condition becomes
$$
\mathbb{E}[r^k] \le e^{-\ell},
$$
   which makes this example the most direct continuous analogue of the Kelly multiplicative update.