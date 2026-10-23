/*
 * Kelly process stopped on leaving [0.5, 2).
 * The annotations are inductive range bounds checked by the frontend.
 * One update from an active state leaves wealth in [0.4, 2.4].
 * refute true marks every finite loop exit for the tailbound interface;
 * both lower and upper exits count as termination, with no fixed horizon.
 */

wealth := 1;
round := 0;

{0.4 <= wealth and wealth <= 2.4 and 0 <= round}
while wealth >= 0.5 and wealth < 2 do
  {0.5 <= wealth and wealth <= 2 and 0 <= round}
  if prob(0.6) then
    {0.5 <= wealth and wealth <= 2 and 0 <= round}
    wealth := wealth * 1.2
  else
    {0.5 <= wealth and wealth <= 2 and 0 <= round}
    wealth := wealth * 0.8
  fi;

  {0.4 <= wealth and wealth <= 2.4 and 0 <= round}
  round := round + 1
od;

{0.4 <= wealth and wealth <= 2.4 and 0 <= round}
refute true;
