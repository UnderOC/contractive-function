random step ~ Uniform(-1, 2);

x := 0;
while x < 20 invariant x <= 22 do
  {x <= 20}
  x := x + step;
od;
{x >= 20 and x <= 22}
refute true;
