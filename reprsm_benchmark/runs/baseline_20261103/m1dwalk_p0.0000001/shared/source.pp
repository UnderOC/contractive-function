/*
 * M1DWalk; paper figure 3; parameters {'p': '0.0000001'}.
 * Provenance status: paper_parameterization. Paper target: lower bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 * exit becomes alive=0; successful completion violates the assertion, as in Figure 3.
 * Current analyzer computes an UPPER bound for this same success event, not the paper lower bound.
 */

{true}
x := 1;
{x = 1}
alive := 1;
{x <= 100 and 0 <= alive and alive <= 1}
while x <= 99 and alive = 1 do
  {x <= 99 and alive = 1}
  if prob(0.0000001) then
    {x <= 99 and alive = 1}
    alive := 0;
  else
    {x <= 99 and alive = 1}
    if prob(0.75) then
      {x <= 99 and alive = 1}
      x := x + 1;
    else
      {x <= 99 and alive = 1}
      x := x - 1;
    fi;
  fi;
od;
{x <= 100 and 0 <= alive and alive <= 1}
assert (alive = 0);
