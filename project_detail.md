# Contractive Function

### Program model
program syntax
```
P::= skip | x:= a | P1;P2 | if E then P1 else P2 | while E do P
a::= r | x | c | a1+a2 | a1*a2 | a1-a2 | 
E::= prob(a) | ¬E1 | E1 ∧ E2 | E1 ∨ E2 | a1 ≤ a2 | a1 < a2 |
```

control flow graph：$(L,X,R,T,\theta)$
- $X$: program variable
- $R$: random variable / sampling variable
- $L$: labels--assignment $L_a$, probabilistic $L_p$, branch $L_b$, start $l_s$, end $l_e$
- $T$: set of transitions in form of $(l, \alpha, l')$. $\alpha$--the transition rule 
	- $l \in L_a$, $\alpha$ is the update function $F_l: Val_x \times Val_r \to Val_x$
	- $l \in L_p$, $\alpha$ is the transition probability, $\alpha \in (0, 1)$
	- $l \in L_b$, $\alpha$ is the guard condition, a propositional polynomial predicate
- $\theta$: the initial state

path: $\{(l_0, x_0), (l_1, x_1), ..., (l_n, x_n)\}$

termination: A run $\omega=\{(l_n,x_n)\}_{n\in\mathbb{N}_0}$ over $P$ is terminating if $l_n=l_e$ for some $n\in\mathbb{N}_0$.
The termination time $T_P$ is a random variable such that for each run $\omega$, $T_P(\omega)$ is the least $n$ with $l_n=l_e$ if it exists, and $\infty$ otherwise.

polynomial invariant (for $P$): a function $I$ assigning a propositional polynomial predicate over $X$ to every label in $G$ such that for all reachable configurations $(\ell,x)$,
$$
x\models I(\ell).
$$

$E(\eta'|\eta) \le \eta - \epsilon, \eta'-\eta \in [a, b]$ => $E(e^{t \cdot \eta'} | \eta) \leq c\cdot e^{t\cdot \eta}, c \in (0,1)$

### contractive loop function
**Definition** 
$$
\mathbb{E}(\eta' \mid \eta) \le c \cdot \eta,\qquad c \in (0,1).
$$

- concavity of log:
$$
  \mathbb{E}(\log \eta' \mid \eta) \le \log(\mathbb{E}(\eta' \mid \eta))
  \qquad \text{(Jensen Inequality)}
  $$
$$
  \Rightarrow\quad \mathbb{E}(\log \eta' \mid \eta) \le \log c + \log \eta,
  \qquad \log c < 0
  $$

- formal:
   $$
  \mathbb{E}(\eta_{t+1} \mid \mathcal{F}_t) \le c\, \eta_t
  \;\Rightarrow\;
  \mathbb{E}(\log \eta_{t+1} \mid \mathcal{F}_t) \le \log \eta_t + \log c
  $$
   可写为类似 ranking supermartingale的形式
  $$
  R_t \;\overset{\mathrm{def}}{=}\; \frac{\log \eta_t}{-\log c}
  \;\Rightarrow\;
  \mathbb{E}(R_{t+1} \mid \mathcal{F}_t) \le R_t - 1
  \qquad \text{(RSM)}
  $$

- bounded increment:
$$
  c' \eta_t \le \eta_{t+1} \le c \eta_t
  \;\Rightarrow\;
  \log c' \le \log \eta_{t+1} - \log \eta_t \le \log c
  $$

### template
$$
\bar{\Phi}_i(x)
=
e^{\,k \log \eta(x) - \ell (n-i)}
=
\eta(x)^k \cdot e^{-\ell (n-i)}
$$
$$
\mathbb{E}(\bar{\Phi}_{i+1}(x') \mid x) \le \bar{\Phi}_i(x)
\;\Rightarrow\;
\mathbb{E}\!\left(\frac{\bar{\Phi}_{i+1}(x')}{\bar{\Phi}_i(x)} \,\middle|\, x\right) \le 1
$$
$$
\Rightarrow\;
\mathbb{E}\!\left(e^{\,k(\log \eta' - \log \eta) + \ell} \,\middle|\, x\right) \le 1
\;\Rightarrow\;
e^\ell \cdot \mathbb{E}\!\left[\left(\frac{\eta'}{\eta}\right)^k \middle| x\right] \le 1
\;\Rightarrow\;
\mathbb{E}\!\left[\left(\frac{\eta'}{\eta}\right)^k \middle| x\right] \le e^{-\ell}
$$
### assertion violation

Violation probability function：

$$
\mathrm{vpf}(\ell,v)
=
\Pr\left[
\exists n.\ \hat{\ell}_n=\ell_f
\mid
\hat{\sigma}_0=(\ell,v)
\right].
$$

根据不动点定理，构造 state function $\Theta$ 满足

$$
\mathrm{ptf}(\Theta)\le \Theta,
$$

则有

$$
\mathrm{vpf}(\ell_{\mathrm{init}},v_{\mathrm{init}})
\le
\Theta(\ell_{\mathrm{init}},v_{\mathrm{init}}).
$$

---

**Contractive Template**

取

$$
\eta_\ell(v)>0,
\qquad
k>0,
\qquad
b_\ell\in\mathbb{R}.
$$

令

$$
g_\ell(v):=\log \eta_\ell(v).
$$

并设

$$
g_{\ell_f}(v)=0,
\qquad
b_{\ell_f}=0.
$$

定义

$$
\Theta(\ell,v)
=
\begin{cases}
0, & \ell=\ell_t,\\[1mm]
1, & \ell=\ell_f,\\[1mm]
\exp\big(k g_\ell(v)+b_\ell\big),
& \ell\notin\{\ell_t,\ell_f\}.
\end{cases}
$$

等价地，

$$
\Theta(\ell,v)
=
e^{b_\ell}\eta_\ell(v)^k.
$$

---

**Moment-Contraction**

（使用了assertion_violation里的程序模型进行表示）

考虑 transition

$$
\tau
=
\langle
\ell^{src},
\varphi,
F_1,\dots,F_m
\rangle,
$$

其中

$$
F_j
=
\langle
\ell^{dst}_j,
p_j,
\mathrm{upd}_j
\rangle.
$$

要求对所有

$$
v\models I(\ell^{src})\wedge \varphi
$$

有

$$

\sum_{j:\ell^{dst}_j\ne \ell_t}
p_j
\mathbb{E}_r
\left[
\exp\left(
k\left(
g_{\ell^{dst}_j}(\mathrm{upd}_j(v,r))
-
g_{\ell^{src}}(v)
\right)
+
b_{\ell^{dst}_j}
-
b_{\ell^{src}}
\right)
\right]
\le 1.

\tag{MC}
$$

写成 $\eta$ 的形式：

$$
\boxed{
\sum_{j:\ell^{dst}_j\ne \ell_t}
p_j
e^{b_{\ell^{dst}_j}-b_{\ell^{src}}}
\mathbb{E}_r
\left[
\left(
\frac{
\eta_{\ell^{dst}_j}(\mathrm{upd}_j(v,r))
}{
\eta_{\ell^{src}}(v)
}
\right)^k
\right]
\le 1.
}
\tag{MC-$\eta$}
$$

---

**Pre Fixed-Point** 

对非终止状态 $(\ell,v)$，

$$
\mathrm{ptf}(\Theta)(\ell,v)
=
\sum_j
p_j
\mathbb{E}_r
\left[
\Theta(\ell^{dst}_j,\mathrm{upd}_j(v,r))
\right].
$$

由于

$$
\Theta(\ell_t,\cdot)=0,
$$

所以

$$
\mathrm{ptf}(\Theta)(\ell,v)
=
\sum_{j:\ell^{dst}_j\ne \ell_t}
p_j
\mathbb{E}_r
\left[
\exp\big(
k g_{\ell^{dst}_j}(\mathrm{upd}_j(v,r))
+
b_{\ell^{dst}_j}
\big)
\right].
$$

同时

$$
\Theta(\ell,v)
=
\exp\big(
k g_\ell(v)+b_\ell
\big).
$$

于是

$$
\frac{
\mathrm{ptf}(\Theta)(\ell,v)
}{
\Theta(\ell,v)
}
=
\sum_{j:\ell^{dst}_j\ne \ell_t}
p_j
\mathbb{E}_r
\left[
\exp\left(
k\left(
g_{\ell^{dst}_j}(\mathrm{upd}_j(v,r))
-
g_\ell(v)
\right)
+
b_{\ell^{dst}_j}
-
b_\ell
\right)
\right].
$$

由 $(MC)$ 得

$$
\frac{
\mathrm{ptf}(\Theta)(\ell,v)
}{
\Theta(\ell,v)
}
\le 1.
$$

因此

$$
\mathrm{ptf}(\Theta)(\ell,v)
\le
\Theta(\ell,v).
$$

即

$$

\mathrm{ptf}(\Theta)\le \Theta.

$$

所以

$$
\boxed{
\Pr[\exists n.\ \hat{\ell}_n=\ell_f]
\le
\Theta(\ell_{\mathrm{init}},v_{\mathrm{init}}).
}
$$
符合前不动点定义。

在contractive function template下的等价定义：

$$
\bar{\Phi}_i(x)
=
\eta(x)^k e^{-\lambda(n-i)}.
$$

则

$$
\bar{\Phi}_{i+1}(x')
=
\eta(x')^k e^{-\lambda(n-i-1)}.
$$

$$
\mathbb{E}[\bar{\Phi}_{i+1}(x')\mid x]
=
e^{-\lambda(n-i-1)}
\mathbb{E}[\eta(x')^k\mid x].
$$

$$
\frac{
\mathbb{E}[\bar{\Phi}_{i+1}(x')\mid x]
}{
\bar{\Phi}_i(x)
}
=
e^\lambda
\mathbb{E}
\left[
\left(
\frac{\eta(x')}{\eta(x)}
\right)^k
\middle|x
\right].
$$

pre fixed-point 条件为

$$
e^\lambda
\mathbb{E}
\left[
\left(
\frac{\eta'}{\eta}
\right)^k
\middle|x
\right]
\le 1.
$$

等价于

$$
\boxed{
\mathbb{E}
\left[
\left(
\frac{\eta'}{\eta}
\right)^k
\middle|x
\right]
\le e^{-\lambda}.
}
$$

---

**Bad Set 归一化**

若坏集合为 $B$，且

$$
x\in B
\implies
\eta(x)\ge H,
$$

取

$$
\Theta_i(x)
=
\left(
\frac{\eta(x)}{H}
\right)^k
e^{-\lambda(n-i)}.
$$

在 $i=n$ 时，

$$
x\in B
\implies
\Theta_n(x)
=
\left(
\frac{\eta(x)}{H}
\right)^k
\ge 1.
$$

于是

$$
\boxed{
\Pr[x_n\in B]
\le
\Theta_0(x_0)
=
\left(
\frac{\eta(x_0)}{H}
\right)^k
e^{-\lambda n}.
}
$$

---

**Ordinary Contraction 到 Moment Contraction 的推导**

假设

$$
\mathbb{E}[\eta'\mid x]\le c\eta(x),
\qquad
0<c<1.
$$

令

$$
R:=\frac{\eta'}{\eta}.
$$

则

$$
\mathbb{E}[R\mid x]\le c.
$$

*case 1.  $k=1$*

取

$$
\lambda=-\log c.
$$

则

$$
\mathbb{E}[R]\le e^{-\lambda}.
$$

因此

$$
\Theta_i(x)
=
\eta(x)c^{n-i}
$$

是合法的 pre fixed-point template。


*case 2.* $0<k\le 1$

由于在 $r\ge 0$ 上 $r\mapsto r^k$ 是 concave，根据 Jensen 不等式：

$$
\mathbb{E}[R^k\mid x]
\le
\left(
\mathbb{E}[R\mid x]
\right)^k
\le
c^k.
$$

取

$$
\lambda=-k\log c.
$$

则

$$
\mathbb{E}[R^k\mid x]
\le
e^{-\lambda}.
$$

因此

$$
\Theta_i(x)
=
\eta(x)^k e^{-(-k\log c)(n-i)}
=
\eta(x)^k c^{k(n-i)}.
$$


*case 3.*  $k>1$

由于在 $r\ge 0$ 上 $r\mapsto r^k$ 是 convex，不能直接使用 Jensen 得到所需的上界。令

$$
Y:=\log \eta'-\log \eta.
$$

则

$$
R^k
=
e^{kY}.
$$

若

$$
Y\in[A,B],
\qquad
\mathbb{E}[Y\mid x]\le \log c,
$$

则 Hoeffding 给出

$$
\mathbb{E}[e^{kY}\mid x]
\le
\exp\left(
k\log c
+
\frac{k^2(B-A)^2}{8}
\right).
$$

因此可取

$$
\lambda_H(k)
=
-k\log c
-
\frac{k^2(B-A)^2}{8}.
$$


如果可以直接优化

$$
\lambda_\star(k)
:=
-\log
\sup_x
\mathbb{E}
\left[
\left(
\frac{\eta'}{\eta}
\right)^k
\middle|x
\right].
$$

则

$$
\mathbb{E}
\left[
\left(
\frac{\eta'}{\eta}
\right)^k
\middle|x
\right]
\le
e^{-\lambda_\star(k)}.
$$

能得到比Hoeffding更紧的上界：

$$
\Pr[\text{violate by }n]
\le
\inf_{k>0}
\exp\left(
k\log\frac{\eta(x_0)}{H}
-
n\lambda_\star(k)
\right).
$$
