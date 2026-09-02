/*
 * Three-round classical Kelly process.
 *
 * Win probability: q = 0.6
 * Even-money payoff: b = 1
 * Kelly fraction: f = (q * (b + 1) - 1) / b = 0.2
 * Win multiplier:  1 + b * f = 1.2
 * Loss multiplier: 1 - f = 0.8
 * Initial wealth:   wealth = 1
 */

{true} wealth := 1;
{wealth = 1} round := 0;

{0 <= wealth and 0 <= round and round <= 3}
while round <= 2 do
  {0 <= wealth and 0 <= round and round <= 2}
  if prob(0.6) then
    {0 <= wealth and 0 <= round and round <= 2}
    wealth := wealth * 1.2
  else
    {0 <= wealth and 0 <= round and round <= 2}
    wealth := wealth * 0.8
  fi;

  {0 <= wealth and 0 <= round and round <= 2}
  round := round + 1
od;

/* After three rounds, wealth <= 0.6 occurs exactly after three losses. */
{0 <= wealth and round = 3}
refute (wealth <= 0.6)
