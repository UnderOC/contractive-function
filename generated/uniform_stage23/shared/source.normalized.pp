{true}
x := 1;
{0 <= x}
while x >= 1 do
  {1 <= x}
  r := Uniform(0, 2);
  {1 <= x and 0 <= r and r <= 2}
  x := r * x;
od;
{0 <= x and x < 1}
refute x <= 0.5;
