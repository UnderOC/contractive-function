/*
 * Shifted 3D quadratic with coupled x,y and anisotropic z; selection (1/4,1/4,1/2).
 * All variables are real. Every finite exit is counted as termination.
 * No fixed horizon is imposed. The quadratic sublevel set is inductive.
 */

x := 2;
y := 0;
z := 1.5;

{0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
while 16 * ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) > 1 do
  {0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
  if prob(0.5) then
    {0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
    if prob(0.5) then
      {0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
      x := 0.5 - 0.5*y
    else
      {0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
      y := -0.5 - 0.5*x
    fi
  else
    {0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
    z := 0.5
  fi
od;

{0 <= ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) and ((x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)) <= 5}
refute true;
