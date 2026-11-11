x := 2;
y := 1;
{-2 <= x - 4 * y and x - 4 * y <= 2 and -1 <= y and y <= 1}
while (x - 4 * y) * (x - 4 * y) + y * y > 0.5 do
  {-2 <= x - 4 * y and x - 4 * y <= 2 and -1 <= y and y <= 1}
  if prob(0.5) then
    {-2 <= x - 4 * y and x - 4 * y <= 2 and -1 <= y and y <= 1}
    x := 0.5 * x - y + 1;
    {0 <= x - y and x - y <= 2 and -1 <= y and y <= 1}
    y := 0.25 * y + 0.125;
  else
    {-2 <= x - 4 * y and x - 4 * y <= 2 and -1 <= y and y <= 1}
    x := 0.5 * x - y - 1;
    {-2 <= x - y and x - y <= 0 and -1 <= y and y <= 1}
    y := 0.25 * y - 0.125;
  fi;
od;
{-2 <= x - 4 * y and x - 4 * y <= 2 and -1 <= y and y <= 1}
refute true;
