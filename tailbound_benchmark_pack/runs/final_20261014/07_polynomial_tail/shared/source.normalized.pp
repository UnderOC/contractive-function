m := 1;
r := Uniform(0, 1);
while r * (m + 1) * (m + 1) <= m * m invariant m >= 1 and r >= 0 and r <= 1 do
  {m >= 1 and r >= 0 and r <= 1 and m * m - r * (m + 1) * (m + 1) >= 0}
  r := Uniform(0, 1);
  {m >= 1 and r >= 0 and r <= 1}
  m := m + 1;
od;
{m >= 1 and r >= 0 and r <= 1 and r * (m + 1) * (m + 1) - m * m >= 0}
refute true;
