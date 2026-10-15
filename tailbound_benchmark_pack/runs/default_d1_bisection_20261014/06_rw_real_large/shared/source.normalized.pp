random r ~ Uniform(0, 1);

x := 200000000;
while x >= 0 invariant x >= -1 do
  {x >= 0}
  if prob(0.7) then
    {x >= 0}
    x := x - r;
  else
    {x >= 0}
    x := x + r;
  fi;
od;
{x >= -1 and x <= 0}
refute true;
