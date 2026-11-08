/*
 * Race; paper figure 1; parameters {'x': 40, 'y': 0}.
 * Provenance status: paper_parameterization. Paper target: upper bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 */

{true}
x := 40;
{x = 40}
y := 0;
{40 <= x and x <= 100 and 0 <= y and y <= 101}
while x <= 99 and y <= 99 do
  {40 <= x and x <= 99 and 0 <= y and y <= 99}
  if prob(0.5) then
    {40 <= x and x <= 99 and 0 <= y and y <= 99}
    x := x + 1;
    {41 <= x and x <= 100 and 0 <= y and y <= 99}
    y := y + 2;
  else
    {40 <= x and x <= 99 and 0 <= y and y <= 99}
    x := x + 1;
  fi;
od;
{40 <= x and x <= 100 and 0 <= y and y <= 101}
assert (x >= 100);
