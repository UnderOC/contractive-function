/*
 * Two invested subaccounts with anticorrelated gross returns.
 * A round multiplies (x,y) by (1.2,0.7) or (0.7,1.2), equally likely.
 * The accounts do not transfer money between themselves.
 * Stop when total wealth leaves [0.5,4); no fixed horizon.
 */

x := 1;
y := 1;

{0 <= x and 0 <= y and 0.35 <= x+y and x+y <= 4.8}
while x+y >= 0.5 and x+y < 4 do
  {0 <= x and 0 <= y and 0.5 <= x+y and x+y <= 4}
  if prob(0.5) then
    {0 <= x and 0 <= y and 0.5 <= x+y and x+y <= 4}
    x := 1.2*x;
    {0 <= x and 0 <= y and 0.5 <= x+y and x+y <= 4.8}
    y := 0.7*y
  else
    {0 <= x and 0 <= y and 0.5 <= x+y and x+y <= 4}
    x := 0.7*x;
    {0 <= x and 0 <= y and 0.35 <= x+y and x+y <= 4}
    y := 1.2*y
  fi
od;

{0 <= x and 0 <= y and 0.35 <= x+y and x+y <= 4.8}
refute true;
