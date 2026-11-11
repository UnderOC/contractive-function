{true}
x := 0;
{100 * x = 0}
y := 0;
{100 * x = 0 and 100 * y = 0}
t := 0;
{0 <= 100 * x and 100 * x <= 50 and 0 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
while 100 * x <= 47 do
  {0 <= 100 * x and 100 * x <= 47 and 0 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
  if 100 * y <= 49 then
    {0 <= 100 * x and 100 * x <= 47 and 0 <= 100 * y and 100 * y <= 49 and 0 <= 100 * t and 100 * t <= 150}
    if prob(0.5) then
      {0 <= 100 * x and 100 * x <= 47 and 0 <= 100 * y and 100 * y <= 49 and 0 <= 100 * t and 100 * t <= 150}
      y := 0.01 + y;
    else
      {0 <= 100 * x and 100 * x <= 47 and 0 <= 100 * y and 100 * y <= 49 and 0 <= 100 * t and 100 * t <= 150}
      skip;
    fi;
  else
    {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
    if prob(0.5) then
      {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
      if prob(0.5) then
        {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
        skip;
      else
        {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
        x := 0.01 + x;
      fi;
    else
      {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
      if prob(0.5) then
        {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
        x := 0.02 + x;
      else
        {0 <= 100 * x and 100 * x <= 47 and 49 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
        x := 0.03 + x;
      fi;
    fi;
  fi;
  {0 <= 100 * x and 100 * x <= 50 and 0 <= 100 * y and 100 * y <= 50 and 0 <= 100 * t and 100 * t <= 150}
  t := 0.01 + t;
  {0 <= 100 * x and 100 * x <= 50 and 0 <= 100 * y and 100 * y <= 50 and 1 <= 100 * t and 100 * t <= 151}
  assert 100 * t <= 150;
od;
