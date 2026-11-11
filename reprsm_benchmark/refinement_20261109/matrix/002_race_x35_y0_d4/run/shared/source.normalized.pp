{true}
x := 0.35;
{100 * x = 35}
y := 0;
{35 <= 100 * x and 100 * x <= 100 and 0 <= 100 * y and 100 * y <= 101}
while 100 * x <= 99 and 100 * y <= 99 do
  {35 <= 100 * x and 100 * x <= 99 and 0 <= 100 * y and 100 * y <= 99}
  if prob(0.5) then
    {35 <= 100 * x and 100 * x <= 99 and 0 <= 100 * y and 100 * y <= 99}
    x := 0.01 + x;
    {36 <= 100 * x and 100 * x <= 100 and 0 <= 100 * y and 100 * y <= 99}
    y := 0.02 + y;
  else
    {35 <= 100 * x and 100 * x <= 99 and 0 <= 100 * y and 100 * y <= 99}
    x := 0.01 + x;
  fi;
od;
{35 <= 100 * x and 100 * x <= 100 and 0 <= 100 * y and 100 * y <= 101}
assert 100 * x >= 100;
