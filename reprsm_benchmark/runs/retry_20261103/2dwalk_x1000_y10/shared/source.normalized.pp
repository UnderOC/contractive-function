{true}
x := 1000;
{x = 1000}
y := 10;
{0 <= x and 0 <= y}
while y >= 1 do
  {0 <= x and 1 <= y}
  if prob(0.5) then
    {0 <= x and 1 <= y}
    if prob(0.75) then
      {0 <= x and 1 <= y}
      x := x + 1;
    else
      {0 <= x and 1 <= y}
      x := x - 1;
    fi;
  else
    {0 <= x and 1 <= y}
    if prob(0.75) then
      {0 <= x and 1 <= y}
      y := y - 1;
    else
      {0 <= x and 1 <= y}
      y := y + 1;
    fi;
  fi;
  {-1 <= x and 0 <= y}
  assert x >= 1;
od;
