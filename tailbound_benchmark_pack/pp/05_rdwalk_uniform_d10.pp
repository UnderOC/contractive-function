/* Concrete d=10 instance; semantics and clock are as in 05_rdwalk_uniform_d1.pp. */
random step ~ Uniform(-1, 2);
x := 0;
while x < 10 invariant x <= 12 do
  {x <= 10}
  x := x + step
od;
{x >= 10 and x <= 12}
refute true;
