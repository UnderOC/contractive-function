wealth := 1;
{0.1 <= wealth and wealth <= 6.4}
while wealth >= 0.25 and wealth < 4 do
  {0.25 <= wealth and wealth <= 4}
  if prob(0.8) then
    {0.25 <= wealth and wealth <= 4}
    wealth := 1.6 * wealth;
  else
    {0.25 <= wealth and wealth <= 4}
    wealth := 0.4 * wealth;
  fi;
od;
{0.1 <= wealth and wealth <= 6.4}
refute true;
