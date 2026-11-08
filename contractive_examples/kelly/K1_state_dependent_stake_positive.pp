/*
 * Kelly-style binary betting with a wealth-dependent stake wealth^2/8.
 * The win probability is 0.4; the bet is intentionally unfavorable.
 * Both lower and upper exits count as termination. No fixed horizon.
 * Certificate and exact checks are in certificates.json and verify_kelly.py.
 */

wealth := 1;

{0.46875 <= wealth and wealth <= 2.5}
while wealth >= 0.5 and wealth < 2 do
  {0.5 <= wealth and wealth <= 2}
  if prob(0.4) then
    {0.5 <= wealth and wealth <= 2}
    wealth := wealth + 0.125*wealth*wealth
  else
    {0.5 <= wealth and wealth <= 2}
    wealth := wealth - 0.125*wealth*wealth
  fi
od;

{0.46875 <= wealth and wealth <= 2.5}
refute true;
