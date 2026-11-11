/*
 * S1: nonnormal triangular affine system with a rare common additive shock.
 * xi=0 with probability 0.98 and xi=+/-0.25 with probability 0.01 each.
 * x is assigned first; y does not depend on old x. These are simultaneous maps.
 * eta=x*x+y*y; target eta<=0.0625; no fixed horizon.
 */
x := 2;
y := 2;

{-2 <= x and x <= 2 and -2 <= y and y <= 2}
while x*x+y*y > 0.0625 do
  {-2 <= x and x <= 2 and -2 <= y and y <= 2}
  if prob(0.98) then
    {-2 <= x and x <= 2 and -2 <= y and y <= 2}
    x := 0.5*x+0.375*y;
    {-2 <= x and x <= 2 and -2 <= y and y <= 2}
    y := 0.5*y
  else
    {-2 <= x and x <= 2 and -2 <= y and y <= 2}
    if prob(0.5) then
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      x := 0.5*x+0.375*y+0.25;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      y := 0.5*y+0.25
    else
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      x := 0.5*x+0.375*y-0.25;
      {-2 <= x and x <= 2 and -2 <= y and y <= 2}
      y := 0.5*y-0.25
    fi
  fi
od;

{-2 <= x and x <= 2 and -2 <= y and y <= 2}
refute true;
