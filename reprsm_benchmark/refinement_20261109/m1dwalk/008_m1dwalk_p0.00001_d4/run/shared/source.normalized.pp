{true}
x := 0.01;
{100 * x = 1}
alive := 1;
{100 * x <= 100 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
while 100 * x <= 99 and alive >= 0.5 do
  {100 * x <= 99 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if prob(0.00001) then
    {100 * x <= 99 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    alive := 0;
  else
    {100 * x <= 99 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.75) then
      {100 * x <= 99 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      x := 0.01 + x;
    else
      {100 * x <= 99 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      x := -0.01 + x;
    fi;
  fi;
od;
{100 * x <= 100 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
assert alive < 0.5;
