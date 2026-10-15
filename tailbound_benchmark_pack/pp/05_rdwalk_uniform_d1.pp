/*
 * Concrete d=1 runtime adaptation of benchmarks/05_rdwalk_uniform.ppl.
 * Each use of step is a fresh continuous Uniform[-1,2] sample.  The source
 * tick/loop counter is omitted and the current clock counts pCFG transitions.
 */

random step ~ Uniform(-1, 2);

x := 0;

while x < 1 invariant x <= 3 do
  {x <= 1}
  x := x + step
od;

{x >= 1 and x <= 3}
refute true;
