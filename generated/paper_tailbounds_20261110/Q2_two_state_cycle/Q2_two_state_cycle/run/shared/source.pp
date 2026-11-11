/*
 * Two-state, one-action-per-state tabular Q-learning with generative sampling.
 * The deterministic transitions alternate the two states. Rewards are 3/4 and 0.
 * Each iteration chooses either state with probability 1/2; alpha=gamma=1/2.
 * Bellman optimum Q*=(1,1/2). Stop at squared error <= 1/64.
 */

q1 := 0;
q2 := 1.5;

{0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
while (q1-1)*(q1-1) + (q2-0.5)*(q2-0.5) > 0.015625 do
  {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
  if prob(0.5) then
    {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
    q1 := 0.5*q1 + 0.25*q2 + 0.375
  else
    {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
    q2 := 0.5*q2 + 0.25*q1
  fi
od;

{0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
refute true;
