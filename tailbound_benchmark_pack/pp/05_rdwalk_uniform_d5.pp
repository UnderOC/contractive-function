/* Concrete d=5 instance; semantics and clock are as in 05_rdwalk_uniform_d1.pp. */
random step ~ Uniform(-1, 2);
x := 0;
while x < 5 invariant x <= 7 do
  {x <= 5}
  x := x + step
od;
{x >= 5 and x <= 7}
refute true;
