{true}
x := 1;
{x = 1}
alive := 1;
{x <= 100 and 0 <= alive and alive <= 1}
while x <= 99 and alive = 1 do
  {x <= 99 and alive = 1}
  if prob(0.0001) then
    {x <= 99 and alive = 1}
    alive := 0;
  else
    {x <= 99 and alive = 1}
    if prob(0.75) then
      {x <= 99 and alive = 1}
      x := x + 1;
    else
      {x <= 99 and alive = 1}
      x := x - 1;
    fi;
  fi;
od;
{x <= 100 and 0 <= alive and alive <= 1}
assert alive = 0;
