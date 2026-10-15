random r ~ Uniform(-1, 0.5);

x := 1;
y := 1;
C := y;
while x >= 1 invariant x >= 0 and y >= 0 and C = y do
  {x >= 1 and y >= 0 and C = y}
  x := x + r;
  {x >= 0 and y >= 0 and C = y}
  if prob(0.5) then
    {x >= 0 and y >= 0 and C = y}
    C := C - 0.5 * y;
    {x >= 0 and y >= 0 and C = 0.5 * y}
    y := 0.5 * y;
  else
    {x >= 0 and y >= 0 and C = y}
    C := C + 0.5 * y;
    {x >= 0 and y >= 0 and C = 1.5 * y}
    y := 1.5 * y;
  fi;
od;
{x >= 0 and x <= 1 and y >= 0 and C = y}
refute true;
