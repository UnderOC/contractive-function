x := 0;
{0 <= x and x <= 1} while x = 0 do
  {x = 0} if prob(0.5) then
    {x = 0} x := 1
  else
    {x = 0} x := 0
  fi
od;
refute true;
