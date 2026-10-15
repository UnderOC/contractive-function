random step ~ Uniform(-1, 2);

x := 0;
while x < 5 invariant x <= 7 do
  {x <= 5}
  x := x + step;
od;
{x >= 5 and x <= 7}
refute true;
