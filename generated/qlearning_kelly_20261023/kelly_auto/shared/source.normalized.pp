wealth := 1;
round := 0;
{0.4 <= wealth and wealth <= 2.4 and 0 <= round}
while wealth >= 0.5 and wealth < 2 do
  {0.5 <= wealth and wealth <= 2 and 0 <= round}
  if prob(0.6) then
    {0.5 <= wealth and wealth <= 2 and 0 <= round}
    wealth := wealth * 1.2;
  else
    {0.5 <= wealth and wealth <= 2 and 0 <= round}
    wealth := wealth * 0.8;
  fi;
  {0.4 <= wealth and wealth <= 2.4 and 0 <= round}
  round := round + 1;
od;
{0.4 <= wealth and wealth <= 2.4 and 0 <= round}
refute true;
