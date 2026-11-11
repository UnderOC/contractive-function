/* Exact coordinates: original = scale * current. */
{true}
x := 0.3;
{1000 * x = 300}
y := 0.1;
{1000 * x = 300 and 1000 * y = 100}
z := 0.15;
{-1 <= 1000 * x and -1 <= 1000 * y and -1 <= 1000 * z}
while 1000 * x >= 0 and 1000 * y >= 0 and 1000 * z >= 0 do
  {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
  assert 1000 * x + 1000 * y + 1000 * z <= 1000;
  {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
  if prob(0.9) then
    {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
    if prob(0.5) then
      {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
      x := -0.001 + x;
      {-1 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
      y := -0.001 + y;
    else
      {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
      z := -0.001 + z;
    fi;
  else
    {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
    if prob(0.5) then
      {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
      x := 0.0001 + x;
      {0.1 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
      y := 0.0001 + y;
    else
      {0 <= 1000 * x and 0 <= 1000 * y and 0 <= 1000 * z}
      z := 0.0001 + z;
    fi;
  fi;
od;
