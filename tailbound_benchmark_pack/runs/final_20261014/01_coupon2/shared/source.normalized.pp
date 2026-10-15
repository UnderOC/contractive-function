c0 := 0;
c1 := 0;
while c0 + c1 < 2 invariant 0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 do
  {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and c0 + c1 <= 2}
  if prob(0.5) then
    {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1}
    c0 := 1;
  else
    {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1}
    c1 := 1;
  fi;
od;
{0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and c0 + c1 >= 2}
refute true;
