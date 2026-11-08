{true}
i := 0;
{i = 0}
alive := 1;
{0 <= i and i <= 41 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
while i <= 40 and alive >= 0.5 do
  {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.995009990004999) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and alive = 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.9999) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.9999) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.997002999) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.994014980014994001) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    i := i + 1;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
od;
{0 <= i and i <= 41 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
assert alive < 0.5;
