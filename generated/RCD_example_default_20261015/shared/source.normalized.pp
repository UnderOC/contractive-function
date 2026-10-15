x := -0.5;
y := 1;
while 4096 * (x * x + x * y + y * y) > 3 invariant -0.5 <= x and x <= 0 and 0 <= y and y <= 1 do
  {-0.5 <= x and x <= 0 and 0 <= y and y <= 1}
  if prob(0.5) then
    {-0.5 <= x and x <= 0 and 0 <= y and y <= 1}
    x := -0.5 * y;
  else
    {-0.5 <= x and x <= 0 and 0 <= y and y <= 1}
    y := -0.5 * x;
  fi;
od;
{-0.5 <= x and x <= 0 and 0 <= y and y <= 1}
refute true;
