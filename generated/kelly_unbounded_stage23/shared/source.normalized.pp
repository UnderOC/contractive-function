{true}
wealth := 1;
{wealth = 1}
round := 0;
{0 < wealth and 0 <= round}
while wealth >= 0.5 do
  {0.5 <= wealth and 0 <= round}
  if prob(0.6) then
    {0.5 <= wealth and 0 <= round}
    wealth := wealth * 1.2;
  else
    {0.5 <= wealth and 0 <= round}
    wealth := wealth * 0.8;
  fi;
  {0 < wealth and 0 <= round}
  round := round + 1;
od;
{0 < wealth and wealth < 0.5 and 0 <= round}
refute wealth <= 0.45;
