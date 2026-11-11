/*
 * One-state, two-action tabular Q-learning. alpha=1/2, gamma=1/2.
 * Action probabilities 3/4 and 1/4. Rewards are {3/8,5/8} and {1/8,3/8}, equally likely.
 * Bellman optimum Q*=(1,3/4). Stop at weighted squared error <= 1/4.
 * Every probabilistic choice is fresh and independent conditional on the state.
 */

q1 := 0;
q2 := 1.25;

{0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
while (q1-1)*(q1-1) + 3*(q2-0.75)*(q2-0.75) > 0.25 do
  {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
  if q1 >= q2 then
    {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
    if prob(0.75) then
      {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q1 := 0.5*q1 + 0.25*q1 + 0.1875
      else
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q1 := 0.5*q1 + 0.25*q1 + 0.3125
      fi
    else
      {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q2 := 0.5*q2 + 0.25*q1 + 0.0625
      else
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q2 := 0.5*q2 + 0.25*q1 + 0.1875
      fi
    fi
  else
    {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
    if prob(0.75) then
      {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q1 := 0.5*q1 + 0.25*q2 + 0.1875
      else
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q1 := 0.5*q1 + 0.25*q2 + 0.3125
      fi
    else
      {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q2 := 0.5*q2 + 0.25*q2 + 0.0625
      else
        {0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
        q2 := 0.5*q2 + 0.25*q2 + 0.1875
      fi
    fi
  fi
od;

{0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25}
refute true;
