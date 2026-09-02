/*
 * Multiplicative process with a fresh uniform sample in every round.
 *
 * Multiplier:       r ~ Uniform(0, 2)
 * Update:           x' = r * x
 * Initial value:    x = 1
 * Loop termination: x < 1
 *
 * The source expression uniform(0, 2) is written as Unif(0, 2) in this
 * .pp dialect.  A temporary variable is needed because random sampling is
 * represented by a probabilistic assignment rather than an expression.
 */

{true} x := 1;

{0 <= x}
while x >= 1 do
  {1 <= x}
  r := Unif(0, 2);

  {1 <= x and 0 <= r and r <= 2}
  x := r * x
od;

/* Analyze the event that the process exits at or below 0.5. */
{0 <= x and x < 1}
refute (x <= 0.5)
