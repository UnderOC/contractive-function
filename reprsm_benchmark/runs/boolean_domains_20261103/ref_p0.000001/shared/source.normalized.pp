{true}
i := 0;
{i = 0}
j := 0;
{i = 0 and j = 0}
k := 0;
{i = 0 and j = 0 and k = 0}
alive := 1;
{0 <= i and i <= 20 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
while i <= 19 and alive >= 0.5 do
  {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  j := 0;
  {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  while j <= 15 and alive >= 0.5 do
    {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    k := 0;
    {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    while k <= 15 and alive >= 0.5 do
      {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 15 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      if prob(0.999997000002999999) then
        {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 15 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
        k := k + 1;
      else
        {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 15 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
        alive := 0;
      fi;
    od;
    {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if alive >= 0.5 then
      {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      j := j + 1;
    else
      {0 <= i and i <= 19 and 0 <= j and j <= 15 and 0 <= k and k <= 16 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
      skip;
    fi;
  od;
  {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.999999) then
      {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      i := i + 1;
    else
      {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 19 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
od;
{0 <= i and i <= 20 and 0 <= j and j <= 16 and 0 <= k and k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
assert alive < 0.5;
