/*
 * Unbounded-horizon Kelly-style multiplicative process.
 *
 * Unlike kelly_simple.pp, this program has no fixed round limit.  It stops
 * only after wealth falls below 0.5, so its termination time is a random,
 * unbounded stopping time.  Moreover, the log-wealth drift is positive:
 *
 *   0.6 * log(1.2) + 0.4 * log(0.8) > 0.
 *
 * Consequently termination is not certain: there is positive probability
 * that wealth never falls below 0.5 and the loop runs forever.
 *
 * The process retains the contractive certificate used by the fixed-round
 * Kelly example.  At successive loop-round boundaries, for
 * C(wealth) = wealth^(-1/2),
 *
 *   E[C(wealth') | wealth]
 *     = rho * C(wealth),
 *
 * where
 *
 *   rho = 0.6 * 1.2^(-1/2) + 0.4 * 0.8^(-1/2)
 *       = sqrt(5)/5 + sqrt(30)/10
 *       < 1.
 *
 * The final refute marks the more severe exit event wealth <= 0.45 as the
 * assertion-failure event.  This event is reachable (four initial losses give
 * wealth = 0.8^4 = 0.4096).  Runs exiting in (0.45, 0.5) terminate normally;
 * runs that never cross 0.5 do not terminate.
 */

{true} wealth := 1;
{wealth = 1} round := 0;

{0 < wealth and 0 <= round}
while wealth >= 0.5 do
  {0.5 <= wealth and 0 <= round}
  if prob(0.6) then
    {0.5 <= wealth and 0 <= round}
    wealth := wealth * 1.2
  else
    {0.5 <= wealth and 0 <= round}
    wealth := wealth * 0.8
  fi;

  {0 < wealth and 0 <= round}
  round := round + 1
od;

{0 < wealth and wealth < 0.5 and 0 <= round}
refute (wealth <= 0.45)
