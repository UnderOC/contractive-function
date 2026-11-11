/*
 * User-provided reference, excluded from the five NEW examples.
 * One shared noise draw per round: Z=0 (0.99), +4 (0.005), -4 (0.005).
 * The y update does not read x, so this assignment order implements the
 * requested simultaneous update exactly.
 */

x := 2;
y := 2;
Z := 0;

{-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
while x*x + y*y > 1 do
  {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
  if prob(0.99) then
    {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
    Z := 0
  else
    {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
    if prob(0.5) then
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
      Z := 4
    else
      {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
      Z := -4
    fi
  fi;
  {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
  x := 0.5*x + 0.25*y + 0.125*Z;
  {-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
  y := 0.5*y + 0.125*Z
od;

{-2 <= x and x <= 2 and -2 <= y and y <= 2 and -4 <= Z and Z <= 4}
refute true;
