{true}
x := 0;
{x = 0}
y := 0;
{x = 0 and y = 0}
t := 0;
{0 <= x and x <= 50 and 0 <= y and y <= 50 and 0 <= t and t <= 200}
while x <= 47 do
  {0 <= x and x <= 47 and 0 <= y and y <= 50 and 0 <= t and t <= 200}
  if y <= 49 then
    {0 <= x and x <= 47 and 0 <= y and y <= 49 and 0 <= t and t <= 200}
    if prob(0.5) then
      {0 <= x and x <= 47 and 0 <= y and y <= 49 and 0 <= t and t <= 200}
      y := y + 1;
    else
      {0 <= x and x <= 47 and 0 <= y and y <= 49 and 0 <= t and t <= 200}
      skip;
    fi;
  else
    {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
    if prob(0.5) then
      {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
      if prob(0.5) then
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
        skip;
      else
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
        x := x + 1;
      fi;
    else
      {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
      if prob(0.5) then
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
        x := x + 2;
      else
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 200}
        x := x + 3;
      fi;
    fi;
  fi;
  {0 <= x and x <= 50 and 0 <= y and y <= 50 and 0 <= t and t <= 200}
  t := t + 1;
  {0 <= x and x <= 50 and 0 <= y and y <= 50 and 1 <= t and t <= 201}
  assert t <= 200;
od;
