{true}
x := 0.4;
{100 * x = 40}
y := 0;
{40 <= 100 * x and 100 * x <= 100 and 0 <= 100 * y and 100 * y <= 101}
while 100 * x <= 99 and 100 * y <= 99 do
  {40 <= 100 * x and 100 * x <= 99 and 0 <= 100 * y and 100 * y <= 99}
  if prob(0.5) then
    {40 <= 100 * x and 100 * x <= 99 and 0 <= 100 * y and 100 * y <= 99}
    x := 0.01 + x;
    {41 <= 100 * x and 100 * x <= 100 and 0 <= 100 * y and 100 * y <= 99}
    y := 0.02 + y;
  else
    {40 <= 100 * x and 100 * x <= 99 and 0 <= 100 * y and 100 * y <= 99}
    x := 0.01 + x;
  fi;
od;
{40 <= 100 * x and 100 * x <= 100 and 0 <= 100 * y and 100 * y <= 101}
assert 100 * x >= 100;
