/*
 * 3DWalk; paper figure 8; parameters {'x': 300, 'y': 100, 'z': 150}.
 * Provenance status: paper_parameterization. Paper target: upper bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 * All three initial values come from Table 1; Figure 8 omits z initialization.
 */

{true}
x := 300;
{x = 300}
y := 100;
{x = 300 and y = 100}
z := 150;
{-1 <= x and -1 <= y and -1 <= z}
while x >= 0 and y >= 0 and z >= 0 do
  {0 <= x and 0 <= y and 0 <= z}
  assert (x + y + z <= 1000);
  {0 <= x and 0 <= y and 0 <= z}
  if prob(0.9) then
    {0 <= x and 0 <= y and 0 <= z}
    if prob(0.5) then
      {0 <= x and 0 <= y and 0 <= z}
      x := x - 1;
      {-1 <= x and 0 <= y and 0 <= z}
      y := y - 1;
    else
      {0 <= x and 0 <= y and 0 <= z}
      z := z - 1;
    fi;
  else
    {0 <= x and 0 <= y and 0 <= z}
    if prob(0.5) then
      {0 <= x and 0 <= y and 0 <= z}
      x := x + 0.1;
      {0.1 <= x and 0 <= y and 0 <= z}
      y := y + 0.1;
    else
      {0 <= x and 0 <= y and 0 <= z}
      z := z + 0.1;
    fi;
  fi;
od;
