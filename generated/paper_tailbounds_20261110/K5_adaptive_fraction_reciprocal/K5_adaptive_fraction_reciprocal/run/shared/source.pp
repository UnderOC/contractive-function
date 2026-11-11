/*
 * Favorable even-money betting with state-dependent fraction
 * f(wealth)=0.125+0.0625*wealth, lying in [0.1875,0.25] in the loop.
 * Both lower and upper exits count as termination; no fixed horizon.
 * The mean and second-moment ratios genuinely depend on wealth.
 */

wealth := 1.5;

{0.8125 <= wealth and wealth <= 2.5}
while wealth >= 1 and wealth < 2 do
  {1 <= wealth and wealth <= 2}
  if prob(0.9) then
    {1 <= wealth and wealth <= 2}
    wealth := 1.125*wealth + 0.0625*wealth*wealth
  else
    {1 <= wealth and wealth <= 2}
    wealth := 0.875*wealth - 0.0625*wealth*wealth
  fi
od;

{0.8125 <= wealth and wealth <= 2.5}
refute true;
