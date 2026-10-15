/*
 * Runtime adaptation of benchmarks/08_escape_200.ppl.
 * First add a fresh Uniform[-1,0.5]; only afterwards test x>=200 and, on
 * that branch, add an independent fresh Uniform[-1,2].
 */

random first_step ~ Uniform(-1, 0.5);
random escape_step ~ Uniform(-1, 2);

x := 0;

while x >= 0 invariant x >= -1 do
  {x >= 0}
  x := x + first_step;
  {x >= -1}
  if x >= 200 then
    {x >= 200}
    x := x + escape_step
  else
    {x >= -1 and x <= 200}
    skip
  fi
od;

{x >= -1 and x <= 0}
refute true;
