x := 1;
while x >= 1 invariant x >= 0 do
  {x >= 1}
  if prob(0.6) then
    {x >= 1}
    x := x - 1;
  else
    {x >= 1}
    x := x + 1;
  fi;
od;
{x >= 0 and x <= 1}
refute true;
