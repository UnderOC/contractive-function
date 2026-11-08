/*
 * One-state, three-action tabular Q-learning. alpha=1/2, gamma=1/4.
 * Action probabilities 1/2,1/4,1/4; deterministic rewards 3/4,1/2,1/4.
 * Bellman optimum Q*=(1,3/4,1/2). The maximum is expanded into branches.
 * Stop at weighted squared error <= 1/64.
 */

q1 := 0;
q2 := 1;
q3 := 1;

{0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
while (q1-1)*(q1-1) + 2*(q2-0.75)*(q2-0.75) + 2*(q3-0.5)*(q3-0.5) > 0.015625 do
  {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
  if q1 >= q2 and q1 >= q3 then
    {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
    if prob(0.5) then
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
      q1 := 0.5*q1 + 0.125*q1 + 0.375
    else
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
        q2 := 0.5*q2 + 0.125*q1 + 0.25
      else
        {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
        q3 := 0.5*q3 + 0.125*q1 + 0.125
      fi
    fi
  else
    {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
    if q2 >= q3 then
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
        q1 := 0.5*q1 + 0.125*q2 + 0.375
      else
        {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
        if prob(0.5) then
          {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
          q2 := 0.5*q2 + 0.125*q2 + 0.25
        else
          {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
          q3 := 0.5*q3 + 0.125*q2 + 0.125
        fi
      fi
    else
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
        q1 := 0.5*q1 + 0.125*q3 + 0.375
      else
        {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
        if prob(0.5) then
          {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
          q2 := 0.5*q2 + 0.125*q3 + 0.25
        else
          {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
          q3 := 0.5*q3 + 0.125*q3 + 0.125
        fi
      fi
    fi
  fi
od;

{0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1}
refute true;
