q1 := 0;
q2 := 2;
{0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
while (q1 - 1.5) * (q1 - 1.5) + (q2 - 1) * (q2 - 1) > 0.0625 do
  {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
  if q1 >= q2 then
    {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
    if prob(0.5) then
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875 * q1 + 0.0625 * q1 + 0.0625;
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875 * q1 + 0.0625 * q1 + 0.125;
      fi;
    else
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875 * q2 + 0.0625 * q1;
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875 * q2 + 0.0625 * q1 + 0.0625;
      fi;
    fi;
  else
    {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
    if prob(0.5) then
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875 * q1 + 0.0625 * q2 + 0.0625;
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q1 := 0.875 * q1 + 0.0625 * q2 + 0.125;
      fi;
    else
      {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
      if prob(0.5) then
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875 * q2 + 0.0625 * q2;
      else
        {0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
        q2 := 0.875 * q2 + 0.0625 * q2 + 0.0625;
      fi;
    fi;
  fi;
od;
{0 <= q1 and q1 <= 2 and 0 <= q2 and q2 <= 2}
refute true;
