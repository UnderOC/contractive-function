x := 2;
y := -1;
{0 <= x * x + x * y + y * y and x * x + x * y + y * y <= 3}
while 64 * (x * x + x * y + y * y) > 1 do
  {0 <= x * x + x * y + y * y and x * x + x * y + y * y <= 3}
  if prob(0.5) then
    {0 <= x * x + x * y + y * y and x * x + x * y + y * y <= 3}
    x := 0.5 * x - 0.25 * y;
  else
    {0 <= x * x + x * y + y * y and x * x + x * y + y * y <= 3}
    y := 0.5 * y - 0.25 * x;
  fi;
od;
{0 <= x * x + x * y + y * y and x * x + x * y + y * y <= 3}
refute true;
