x := -0.5;
y := 1;
{(x + 0.5 * y) * (y + 0.5 * x) = 0}
while 4096 * (x * x + x * y + y * y) > 3 do
  {(x + 0.5 * y) * (y + 0.5 * x) = 0}
  if prob(0.5) then
    {(x + 0.5 * y) * (y + 0.5 * x) = 0}
    x := -0.5 * y;
  else
    {(x + 0.5 * y) * (y + 0.5 * x) = 0}
    y := -0.5 * x;
  fi;
od;
{(x + 0.5 * y) * (y + 0.5 * x) = 0}
refute true;
