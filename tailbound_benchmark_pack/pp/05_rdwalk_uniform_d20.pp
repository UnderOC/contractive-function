/* Concrete d=20 instance; semantics and clock are as in 05_rdwalk_uniform_d1.pp. */
random step ~ Uniform(-1, 2);
x := 0;
while x < 20 invariant x <= 22 do
  {x <= 20}
  x := x + step
od;
{x >= 20 and x <= 22}
refute true;
