{true}
x := 100;
{x = 100}
y := 150;
{x = 100 and y = 150}
z := 200;
{-1 <= x and x <= 1000.1 and -1 <= y and y <= 1000.1 and -1 <= z and z <= 1000.1}
while x >= 0 and y >= 0 and z >= 0 do
  {0 <= x and x <= 1000.1 and 0 <= y and y <= 1000.1 and 0 <= z and z <= 1000.1}
  assert x + y + z <= 1000;
  {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
  if prob(0.9) then
    {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
    if prob(0.5) then
      {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
      x := x - 1;
      {-1 <= x and x <= 999 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
      y := y - 1;
    else
      {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
      z := z - 1;
    fi;
  else
    {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
    if prob(0.5) then
      {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
      x := x + 0.1;
      {0.1 <= x and x <= 1000.1 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
      y := y + 0.1;
    else
      {0 <= x and x <= 1000 and 0 <= y and y <= 1000 and 0 <= z and z <= 1000}
      z := z + 0.1;
    fi;
  fi;
od;
