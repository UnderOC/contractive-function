x := 2;
y := 2;
z := 2;
{-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
while x * x + y * y + z * z > 0.25 do
  {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
  if prob(0.875) then
    {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
    if prob(0.5) then
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      y := 0.25 * y - 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      z := 0.25 * z + 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      x := 0.25 * x + 0.125;
    else
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      y := 0.25 * y + 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      z := 0.25 * z - 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      x := 0.25 * x - 0.125;
    fi;
  else
    {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
    if prob(0.5) then
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      y := 0.75 * x - 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      z := 0.75 * x + 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      x := 0.75 * x + 0.125;
    else
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      y := 0.75 * x + 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      z := 0.75 * x - 0.125;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
      x := 0.75 * x - 0.125;
    fi;
  fi;
od;
{-2 <= x and x <= 2 and -2 <= y and y <= 2 and -2 <= z and z <= 2}
refute true;
