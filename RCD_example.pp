/*
 * Randomized coordinate descent example.
 * The source guard (x*x + x*y + y*y)/2 > 3/8192 is written
 * equivalently as 4096*(x*x + x*y + y*y) > 3, without division.
 * if prob(0.5) is a fresh independent Bernoulli(1/2) choice per round.
 * x and y are real-valued. There are no box or Boolean domain restrictions.
 * Location annotations give the inductive equality invariant:
 * (x + y/2)*(y + x/2) = 0.
 * Initialization is fixed; the proof domain covers all real states satisfying
 * the annotation, rather than only states reachable from that initialization.
 * refute true marks every finite loop exit for the tailbound analysis.
 */

x := -0.5;
y := 1;

{(x + 0.5*y)*(y + 0.5*x) = 0}
while 4096 * (x*x + x*y + y*y) > 3 do
  {(x + 0.5*y)*(y + 0.5*x) = 0}
  if prob(0.5) then
    {(x + 0.5*y)*(y + 0.5*x) = 0}
    x := -0.5 * y
  else
    {(x + 0.5*y)*(y + 0.5*x) = 0}
    y := -0.5 * x
  fi
od;

{(x + 0.5*y)*(y + 0.5*x) = 0}
refute true;
