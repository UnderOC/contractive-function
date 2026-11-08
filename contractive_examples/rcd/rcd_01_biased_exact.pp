/*
 * Biased two-coordinate descent for f=x^2+x*y+y^2; selection (1/4,3/4).
 * All variables are real. Every finite exit is counted as termination.
 * No fixed horizon is imposed. The quadratic sublevel set is inductive.
 */

x := 1;
y := 1;

{0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 3}
while 16 * (x*x + x*y + y*y) > 1 do
  {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 3}
  if prob(0.25) then
    {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 3}
    x := -0.5*y
  else
    {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 3}
    y := -0.5*x
  fi
od;

{0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 3}
refute true;
