{true}
x := 50;
{-2 <= x and x <= 1001}
while x >= 0 do
  {0 <= x and x <= 1001}
  assert x <= 1000;
  {0 <= x and x <= 1000}
  if prob(0.5) then
    {0 <= x and x <= 1000}
    x := x - 2;
  else
    {0 <= x and x <= 1000}
    x := x + 1;
  fi;
od;
