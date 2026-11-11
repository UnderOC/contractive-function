/*
 * Coupled quadratic, random coordinate and independent random step length (half or exact).
 * All variables are real. Every finite exit is counted as termination.
 * No fixed horizon is imposed. The quadratic sublevel set is inductive.
 */

x := 1;
y := -1;

{0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
while 4 * (x*x + x*y + y*y) > 3 do
  {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
  if prob(0.5) then
    {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
    if prob(0.5) then
      {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
      x := 0.5*x - 0.25*y
    else
      {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
      x := -0.5*y
    fi
  else
    {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
    if prob(0.5) then
      {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
      y := 0.5*y - 0.25*x
    else
      {0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
      y := -0.5*x
    fi
  fi
od;

{0 <= (x*x + x*y + y*y) and (x*x + x*y + y*y) <= 1}
refute true;
