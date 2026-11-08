/*
 * 1DWalk; paper figure 6; parameters {'x': 10}.
 * Provenance status: paper_parameterization. Paper target: upper bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 */

{true}
x := 10;
{-2 <= x and x <= 1001}
while x >= 0 do
  {0 <= x and x <= 1001}
  assert (x <= 1000);
  {0 <= x and x <= 1000}
  if prob(0.5) then
    {0 <= x and x <= 1000}
    x := x - 2;
  else
    {0 <= x and x <= 1000}
    x := x + 1;
  fi;
od;
