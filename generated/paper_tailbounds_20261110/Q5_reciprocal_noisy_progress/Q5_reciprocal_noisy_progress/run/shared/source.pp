/*
 * One-state, two-action Q-learning with random rewards. alpha=gamma=1/2.
 * Each action is selected with probability 1/2. Rewards are {1/2,3/4} and {1/4,1/2}.
 * Each reward choice is fair. Bellman optimum Q*=(5/4,1).
 * Stop when q1+q2 reaches 5/8, a progress milestone from the zero initialization.
 * The full box is inductive; low-reward updates may decrease q1+q2 while the guard holds.
 */

q1 := 0;
q2 := 0;

{0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
while q1 + q2 < 0.625 do
  {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
  if q1 >= q2 then
    {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
    if prob(0.5) then
      {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q1 := 0.5*q1 + 0.25*q1 + 0.25
      else
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q1 := 0.5*q1 + 0.25*q1 + 0.375
      fi
    else
      {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q2 := 0.5*q2 + 0.25*q1 + 0.125
      else
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q2 := 0.5*q2 + 0.25*q1 + 0.25
      fi
    fi
  else
    {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
    if prob(0.5) then
      {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q1 := 0.5*q1 + 0.25*q2 + 0.25
      else
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q1 := 0.5*q1 + 0.25*q2 + 0.375
      fi
    else
      {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
      if prob(0.5) then
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q2 := 0.5*q2 + 0.25*q2 + 0.125
      else
        {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
        q2 := 0.5*q2 + 0.25*q2 + 0.25
      fi
    fi
  fi
od;

{0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
refute true;
