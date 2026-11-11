q1 := 0;
q2 := 1.5;
{0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
while (q1 - 1) * (q1 - 1) + (q2 - 0.5) * (q2 - 0.5) > 0.015625 do
  {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
  if prob(0.5) then
    {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
    q1 := 0.5 * q1 + 0.25 * q2 + 0.375;
  else
    {0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
    q2 := 0.5 * q2 + 0.25 * q1;
  fi;
od;
{0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5}
refute true;
