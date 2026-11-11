# Exact invariant certification for tail analysis

The tail pipeline and the Cauchy/reciprocal random-round compiler use
`analysis.invariant_certification.prepare_certified_program`. It calls the
existing `semantics.prepare_program` with an `InvariantProver` callback. The
semantic layer still derives every preservation obligation from source CFG
transitions, updates, support regions and destination annotations. Source
annotations are not assumed to be true.

The callback tries:

1. The original exact Farkas/affine-equality checks.
2. An exact quadratic check after affine equality elimination. It constructs
   the rational matrix for `h = [1,x]^T Q [1,x]` and checks PSD, including
   singular matrices. It also tries subtracting a nonnegative constant multiple
   of one existing inequality before this check. Candidate constants are one
   and positive ratios of matching polynomial coefficients; this is a limited
   search, not a complete quadratic implication solver.
3. The previous shifted-monomial and bounded-generator-product rules.
4. Putinar SOS models of orders one and two, using the existing conic builder,
   CVXPY/MOSEK solver and rational reconstruction. A numerical solver status
   alone never establishes an invariant.

For example, with `f=x^2+x*y+y^2` and `0<=f<=3`, the update `x:=-y/2`
requires both `3*y^2/4>=0` and `3-3*y^2/4>=0`. The second obligation has the
identity `3-3*y^2/4 = (3-f)+(x+y/2)^2`. Both are handled by step two without a
numerical solve. This also avoids a slow generator-product LP on shifted RCD
quadratics.

Each preparation has a local cache and a 15-second soft deadline for SOS
fallback, with at most 3 seconds per solver call. SOS models are limited to
order two, 32 generators, PSD dimension 28 and 1500 decisions. These are
preparation safeguards; no additional tail-template search budget is granted.
The exact algebraic stages and one symbolic/backend operation are not
preempted, so the deadline is not a hard wall-clock limit. Failed recovery,
unsupported degree, missing backend and resource exhaustion remain unknown
and cannot authorize use of an invariant. The diagnostic retains the failed
obligation's reason.

New proofs have method `exact_invariant_sos` and contain the original domain
and conclusion, the equality-reduced domain and conclusion, and either a
quadratic remainder witness or the SOS order/model/exact rational values.
They are saved inside the existing `domain_evidence.json` and random-round
evidence. No floating-point values are needed to replay them.

`prepare_certified_program(..., saved_evidence=...)` and
`prepare_random_round(..., invariant_evidence=...)` rebuild obligations from
source and check the saved certificates. Quadratic matrices and conic models
are reconstructed, exact identities and PSD are rechecked, and the complete
program evidence must match. Replay does not synthesize missing witnesses or
call the numerical solver. The public workflow verifier and the standalone
Cauchy/reciprocal verify/evaluate commands use these replay paths. Old evidence
using only the existing algebraic rules remains supported.

The low-level `semantics.prepare_program` default retains its existing
certification rules; assertion analysis is archived on develop. Random initialization and
probability checks also retain their existing semantics; this extension targets
inductive invariant preservation in tail analysis.
