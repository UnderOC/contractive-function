{true}
x := 35;
{x = 35}
y := 0;
{35 <= x and x <= 100 and 0 <= y and y <= 101}
while x <= 99 and y <= 99 do
  {35 <= x and x <= 99 and 0 <= y and y <= 99}
  if prob(0.5) then
    {35 <= x and x <= 99 and 0 <= y and y <= 99}
    x := x + 1;
    {36 <= x and x <= 100 and 0 <= y and y <= 99}
    y := y + 2;
  else
    {35 <= x and x <= 99 and 0 <= y and y <= 99}
    x := x + 1;
  fi;
od;
{35 <= x and x <= 100 and 0 <= y and y <= 101}
assert x >= 100;
