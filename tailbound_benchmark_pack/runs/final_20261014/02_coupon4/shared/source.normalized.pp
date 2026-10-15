c0 := 0;
c1 := 0;
c2 := 0;
c3 := 0;
while c0 + c1 + c2 + c3 < 4 invariant 0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1 do
  {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1 and c0 + c1 + c2 + c3 <= 4}
  if prob(0.5) then
    {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1}
    if prob(0.5) then
      {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1}
      c0 := 1;
    else
      {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1}
      c1 := 1;
    fi;
  else
    {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1}
    if prob(0.5) then
      {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1}
      c2 := 1;
    else
      {0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1}
      c3 := 1;
    fi;
  fi;
od;
{0 <= c0 and c0 <= 1 and 0 <= c1 and c1 <= 1 and 0 <= c2 and c2 <= 1 and 0 <= c3 and c3 <= 1 and c0 + c1 + c2 + c3 >= 4}
refute true;
