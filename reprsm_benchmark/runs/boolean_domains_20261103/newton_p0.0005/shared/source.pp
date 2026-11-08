/*
 * Newton; paper figure 11; parameters {'p': '0.0005'}.
 * Provenance status: paper_parameterization. Paper target: lower bound.
 * Annotations are sound interval overapproximations, checked by prepare_program.
 * Sequential updates replace tuple updates only when RHS variables do not cross-depend.
 * Missing final assertion is supplied using Section 3.3 hardware-success event.
 * exit is encoded by a flag; all subsequent hazards/updates are skipped when alive=0.
 * No numerical Newton update is invented: the paper explicitly abstracts it to skip.
 */

{true}
i := 0;
{i = 0}
alive := 1;
{0 <= i and i <= 41 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
while i <= 40 and alive >= 0.5 do
  {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.99750249875031246875) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and alive = 0.5}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.9999) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.9999) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.998500749875) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    if prob(0.997003747500937312515625) then
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      skip;
    else
      {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
      alive := 0;
    fi;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
  {0 <= i and i <= 40 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
  if alive >= 0.5 then
    {0 <= i and i <= 40 and 0.5 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
    i := i + 1;
  else
    {0 <= i and i <= 40 and 0 <= alive and alive <= 0.5 and (alive = 0 or alive = 1)}
    skip;
  fi;
od;
{0 <= i and i <= 41 and 0 <= alive and alive <= 1 and (alive = 0 or alive = 1)}
assert (alive < 0.5);
