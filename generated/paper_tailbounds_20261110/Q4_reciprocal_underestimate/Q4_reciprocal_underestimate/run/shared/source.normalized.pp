q1 := 0;
q2 := 0;
{0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
while q1 + q2 < 1.5 do
  {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
  if q1 >= q2 then
    {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
    if prob(0.5) then
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
      q1 := 0.5 * q1 + 0.25 * q1 + 0.25;
    else
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
      q2 := 0.5 * q2 + 0.25 * q1 + 0.25;
    fi;
  else
    {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
    if prob(0.5) then
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
      q1 := 0.5 * q1 + 0.25 * q2 + 0.25;
    else
      {0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
      q2 := 0.5 * q2 + 0.25 * q2 + 0.25;
    fi;
  fi;
od;
{0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1}
refute true;
