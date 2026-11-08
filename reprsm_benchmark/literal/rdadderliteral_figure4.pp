/*
 * RdAdderLiteral; paper figure 4; parameters {'literal_assertion': 'x <= 200'}.
 * Provenance status: literal_degenerate_zero_violation. Paper target: upper bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 * The assertion remains inside the loop as printed. This literal figure has zero violation probability.
 * It does not represent any of the three Table 1 deviation events.
 */

{true}
i := 0;
{i = 0}
x := 0;
{0 <= i and 0 <= x and x <= 100}
while x <= 99 do
  {0 <= i and 0 <= x and x <= 99}
  if prob(0.5) then
    {0 <= i and 0 <= x and x <= 99}
    i := i + 1;
    {1 <= i and 0 <= x and x <= 99}
    x := x + 1;
  else
    {0 <= i and 0 <= x and x <= 99}
    i := i + 1;
  fi;
  {1 <= i and 0 <= x and x <= 100}
  assert (x <= 200);
od;
