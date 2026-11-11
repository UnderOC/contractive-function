/*
 * A fixed-fraction asymmetric bet followed by a contribution of 0.125.
 * Win gross multiplier 1.25 (probability 0.8); loss multiplier 0.875.
 * Losing at wealth=1 leaves wealth unchanged, so there is no fixed horizon.
 * Stop when wealth reaches 4. The lower guard is an inductive bound.
 */

wealth := 1;

{1 <= wealth and wealth <= 5.125}
while wealth >= 1 and wealth < 4 do
  {1 <= wealth and wealth <= 4}
  if prob(0.8) then
    {1 <= wealth and wealth <= 4}
    wealth := 1.25*wealth + 0.125
  else
    {1 <= wealth and wealth <= 4}
    wealth := 0.875*wealth + 0.125
  fi
od;

{1 <= wealth and wealth <= 5.125}
refute true;
