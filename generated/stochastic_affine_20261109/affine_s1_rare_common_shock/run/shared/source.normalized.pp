x := 2;
y := 2;
{-2 <= x and x <= 2 and -2 <= y and y <= 2}
while x * x + y * y > 0.0625 do
  {-2 <= x and x <= 2 and -2 <= y and y <= 2}
  if prob(0.98) then
    {-2 <= x and x <= 2 and -2 <= y and y <= 2}
    x := 0.5 * x + 0.375 * y;
    {-2 <= x and x <= 2 and -2 <= y and y <= 2}
    y := 0.5 * y;
  else
    {-2 <= x and x <= 2 and -2 <= y and y <= 2}
    if prob(0.5) then
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      x := 0.5 * x + 0.375 * y + 0.25;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      y := 0.5 * y + 0.25;
    else
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      x := 0.5 * x + 0.375 * y - 0.25;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      y := 0.5 * y - 0.25;
    fi;
  fi;
od;
{-2 <= x and x <= 2 and -2 <= y and y <= 2}
refute true;
