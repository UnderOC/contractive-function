/*
 * Prspeed; paper figure 10; parameters {'T_greater_than': 150}.
 * Provenance status: paper_parameterization. Paper target: upper bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 * Four equiprobable updates are encoded by two fair choices; time counts original iterations.
 */

{true}
x := 0;
{x = 0}
y := 0;
{x = 0 and y = 0}
t := 0;
{0 <= x and x <= 50 and 0 <= y and y <= 50 and 0 <= t and t <= 150}
while x <= 47 do
  {0 <= x and x <= 47 and 0 <= y and y <= 50 and 0 <= t and t <= 150}
  if y <= 49 then
    {0 <= x and x <= 47 and 0 <= y and y <= 49 and 0 <= t and t <= 150}
    if prob(0.5) then
      {0 <= x and x <= 47 and 0 <= y and y <= 49 and 0 <= t and t <= 150}
      y := y + 1;
    else
      {0 <= x and x <= 47 and 0 <= y and y <= 49 and 0 <= t and t <= 150}
      skip;
    fi;
  else
    {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
    if prob(0.5) then
      {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
      if prob(0.5) then
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
        skip;
      else
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
        x := x + 1;
      fi;
    else
      {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
      if prob(0.5) then
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
        x := x + 2;
      else
        {0 <= x and x <= 47 and 49 <= y and y <= 50 and 0 <= t and t <= 150}
        x := x + 3;
      fi;
    fi;
  fi;
  {0 <= x and x <= 50 and 0 <= y and y <= 50 and 0 <= t and t <= 150}
  t := t + 1;
  {0 <= x and x <= 50 and 0 <= y and y <= 50 and 1 <= t and t <= 151}
  assert (t <= 150);
od;
