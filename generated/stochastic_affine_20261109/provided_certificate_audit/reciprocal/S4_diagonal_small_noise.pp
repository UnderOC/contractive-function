/*
 * S4: stable diagonal dynamics with small additive noise.
 * Each iteration resamples z independently: zero unless the rare branch fires,
 * then +1 or -1 with equal conditional probability.
 * nx stores the next x value so both state updates use the same old x,y.
 * The loop ends on first entry into the target ball; there is no time cap.
 */
x := 0.75;
y := 0.5;

{x*x + y*y <= 1}
while x*x + y*y > 0.25 do
  {x*x + y*y <= 1}
  if prob(0.125) then
    {x*x + y*y <= 1}
    if prob(0.5) then
      {x*x + y*y <= 1}
      z := 1
    else
      {x*x + y*y <= 1}
      z := -1
    fi
  else
    {x*x + y*y <= 1}
    z := 0
  fi;
  {x*x + y*y <= 1 and z*z <= 1}
  nx := 0.5*x + 0.25*z;
  {x*x + y*y <= 1 and z*z <= 1 and nx = 0.5*x + 0.25*z}
  y := 0.5*y;
  {nx*nx + y*y <= 1}
  x := nx
od;

{x*x + y*y <= 1}
refute true;
