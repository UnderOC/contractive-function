x := 1;
y := 1;
{0 <= x and 0 <= y and 0.35 <= x + y and x + y <= 4.8}
while x + y >= 0.5 and x + y < 4 do
  {0 <= x and 0 <= y and 0.5 <= x + y and x + y <= 4}
  if prob(0.5) then
    {0 <= x and 0 <= y and 0.5 <= x + y and x + y <= 4}
    x := 1.2 * x;
    {0 <= x and 0 <= y and 0.5 <= x + y and x + y <= 4.8}
    y := 0.7 * y;
  else
    {0 <= x and 0 <= y and 0.5 <= x + y and x + y <= 4}
    x := 0.7 * x;
    {0 <= x and 0 <= y and 0.35 <= x + y and x + y <= 4}
    y := 1.2 * y;
  fi;
od;
{0 <= x and 0 <= y and 0.35 <= x + y and x + y <= 4.8}
refute true;
