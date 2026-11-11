x := 2;
y := 0;
z := 0;
{x >= 0 and y >= 0 and y <= 1}
while x >= 1 do
  {x >= 1 and y >= 0 and y <= 1}
  z := Bernoulli(0.01);
  {x >= 1 and y >= 0 and y <= 1 and z >= 0 and z <= 1}
  z := 10 * z;
  {x >= 1 and y >= 0 and y <= 1 and z >= 0 and z <= 10}
  x := x * (0.3 + 0.1 * y + (0.05 + 0.05 * y) * z);
  {x >= 0 and z >= 0 and z <= 10}
  y := 0.1 * z;
od;
refute true;
