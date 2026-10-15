random step ~ Uniform(-1, 2);

x := 0;
while x < 1 invariant x <= 3 do
  {x <= 1}
  x := x + step;
od;
{x >= 1 and x <= 3}
refute true;
