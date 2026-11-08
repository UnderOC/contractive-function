{true}
i := 0;
{i = 0}
x := 0;
{0 <= i and 0 <= x and x <= 100}
while x <= 99 do
  {0 <= i and 0 <= x and x <= 99}
  if prob(0.5) then
    {0 <= i and 0 <= x and x <= 99}
    i := i + 1;
    {1 <= i and 0 <= x and x <= 99}
    x := x + 1;
  else
    {0 <= i and 0 <= x and x <= 99}
    i := i + 1;
  fi;
  {1 <= i and 0 <= x and x <= 100}
  assert x <= 200;
od;
