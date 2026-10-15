random step ~ Uniform(-1, 2);

x := 0;
while x < 10 invariant x <= 12 do
  {x <= 10}
  x := x + step;
od;
{x >= 10 and x <= 12}
refute true;
