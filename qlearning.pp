/*
 * One-state, two-action Q-learning with independent finite random rewards.
 * gamma=1/2, alpha=1/8, Q0=(0,2), Q*=(3/2,1).
 * Stop on first reaching squared error <= 1/16.
 * max(q1,q2) is expanded as a deterministic branch. Each action and reward
 * choice is a fresh fair probabilistic branch; m and r are inlined.
 * The checked box invariant is [0,2]^2. No potential coefficients or
 * contraction factor are supplied to the synthesizer by this input.
 * refute true marks all finite exits for the tailbound interface.
 */

q1 := 0;
q2 := 2;

{0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
while (q1-1.5)*(q1-1.5) + (q2-1)*(q2-1) > 0.0625 do
  {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
  if q1 >= q2 then
    {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
    if prob(0.5) then
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875*q1 + 0.0625*q1 + 0.0625
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875*q1 + 0.0625*q1 + 0.125
      fi
    else
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875*q2 + 0.0625*q1
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875*q2 + 0.0625*q1 + 0.0625
      fi
    fi
  else
    {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
    if prob(0.5) then
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875*q1 + 0.0625*q2 + 0.0625
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875*q1 + 0.0625*q2 + 0.125
      fi
    else
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875*q2 + 0.0625*q2
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875*q2 + 0.0625*q2 + 0.0625
      fi
    fi
  fi
od;

{0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
refute true;
