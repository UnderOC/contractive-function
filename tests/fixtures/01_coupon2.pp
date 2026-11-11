/*
 * Runtime adaptation of benchmarks/01_coupon2.ppl.
 * The loop-iteration ghost C is omitted.  refute true makes every finite exit
 * a failure event for the current late_bad_exit tail analysis.  The clock is
 * therefore pCFG transitions from program entry, not the source C counter.
 */

c0 := 0;
c1 := 0;

while c0 + c1 < 2
invariant 0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1
do
  {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and c0 + c1 <= 2}
  if prob(0.5) then
    {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1}
    c0 := 1
  else
    {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1}
    c1 := 1
  fi
od;

{0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and c0 + c1 >= 2}
refute true;
