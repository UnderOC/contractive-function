{true}
x := 0;
{x = 0}
t := 0;
{x <= 100 and 0 <= t}
while x <= 99 do
  {x <= 99 and 0 <= t}
  if prob(0.75) then
    {x <= 99 and 0 <= t}
    x := x + 1;
  else
    {x <= 99 and 0 <= t}
    x := x - 1;
  fi;
  {x <= 100 and 0 <= t}
  t := t + 1;
od;
{99 <= x and x <= 100 and 0 <= t}
assert t <= 500;
