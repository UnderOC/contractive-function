/* Exact coordinates: original = scale * current. */
{true}
i := 0;
{100 * i = 0}
j := 0;
{100 * i = 0 and 100 * j = 0}
k := 0;
{100 * i = 0 and 100 * j = 0 and 100 * k = 0}
alive := 1;
{0 <= 100 * i and 100 * i <= 20 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
while 100 * i <= 19 and alive >= 0.5 do
  {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  j := 0;
  {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  while 100 * j <= 15 and alive >= 0.5 do
    {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    k := 0;
    {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    while 100 * k <= 15 and alive >= 0.5 do
      {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 15 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      if prob(0.999999700000029999999) then
        {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 15 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
        k := 0.01 + k;
      else
        {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 15 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
        alive := 0;
      fi;
    od;
    {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if alive >= 0.5 then
      {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      j := 0.01 + j;
    else
      {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 15 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
      skip;
    fi;
  od;
  {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.9999999) then
      {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      i := 0.01 + i;
    else
      {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= 100 * i and 100 * i <= 19 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
od;
{0 <= 100 * i and 100 * i <= 20 and 0 <= 100 * j and 100 * j <= 16 and 0 <= 100 * k and 100 * k <= 16 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
assert alive < 0.5;
