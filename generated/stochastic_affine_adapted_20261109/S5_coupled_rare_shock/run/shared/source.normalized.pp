x := 0.02;
y := 0.86;
z := 0;
nx := 0;
{x * x + y * y <= 1}
while x * x + y * y > 0.5 do
  {x * x + y * y <= 1}
  if prob(0.01) then
    {x * x + y * y <= 1}
    if prob(0.5) then
      {x * x + y * y <= 1}
      z := 1;
    else
      {x * x + y * y <= 1}
      z := -1;
    fi;
  else
    {x * x + y * y <= 1}
    z := 0;
  fi;
  {x * x + y * y <= 1 and z * z <= 1}
  nx := 0.42 * x + 0.06 * y + 0.225 * z;
  {x * x + y * y <= 1 and z * z <= 1 and nx = 0.42 * x + 0.06 * y + 0.225 * z}
  y := 0.06 * x + 0.455 * y + 0.3 * z;
  {nx * nx + y * y <= 1}
  x := nx;
od;
{x * x + y * y <= 1}
refute true;
