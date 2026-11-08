/*
 * Anisotropic shifted quadratic, exact random coordinate minimization, stopped at f<=15/8.
 * All variables are real. Every finite exit is counted as termination.
 * No fixed horizon is imposed. The quadratic sublevel set is inductive.
 */

x := 2.5;
y := -1.75;

{0 <= ((x-1)*(x-1) + 4*(y+2)*(y+2)) and ((x-1)*(x-1) + 4*(y+2)*(y+2)) <= 2.5}
while 8 * ((x-1)*(x-1) + 4*(y+2)*(y+2)) > 15 do
  {0 <= ((x-1)*(x-1) + 4*(y+2)*(y+2)) and ((x-1)*(x-1) + 4*(y+2)*(y+2)) <= 2.5}
  if prob(0.5) then
    {0 <= ((x-1)*(x-1) + 4*(y+2)*(y+2)) and ((x-1)*(x-1) + 4*(y+2)*(y+2)) <= 2.5}
    x := 1
  else
    {0 <= ((x-1)*(x-1) + 4*(y+2)*(y+2)) and ((x-1)*(x-1) + 4*(y+2)*(y+2)) <= 2.5}
    y := -2
  fi
od;

{0 <= ((x-1)*(x-1) + 4*(y+2)*(y+2)) and ((x-1)*(x-1) + 4*(y+2)*(y+2)) <= 2.5}
refute true;
