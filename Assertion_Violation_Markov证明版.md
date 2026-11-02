# Assertion-Violation Bounds via Contractive Potentials and Markov's Inequality

## 1. Program Semantics and a General Violation Bound

### 1.1 Model and Notation

A program state is $s=(\ell,\mathbf v)$. The normal terminal location $\ell_t$ and failure location $\ell_f$ are absorbing. A transition from $\ell$ has the form

$$
\tau=\langle\ell,\varphi,F_1,\ldots,F_m\rangle,
\qquad
F_j=\langle\ell_j,p_j,\mathrm{upd}_j\rangle,
\qquad
p_j>0,\quad \sum_{j=1}^m p_j=1.
\tag{1.1}
$$

When $\mathbf v\models\varphi$, branch $j$ produces $S'=(\ell_j,\mathrm{upd}_j(\mathbf v,\mathbf r))$. Write $\mathbb E_s$ for the one-step expectation under an enabled transition, including branch selection and random updates. Assume measurable transitions and an inductive invariant $I$ containing the deterministic initial state $s_0$. For each enabled transition, the current state determines its conditional sampling law. If choices are nondeterministic, fix any scheduler; all conditions and suprema below range over every enabled transition, giving bounds uniform over schedulers.

Define

$$
\begin{aligned}
\mathcal D&:=\{(\ell,\mathbf v)\in I:\ell\notin\{\ell_t,\ell_f\}\},\\
\mathcal B&:=\{(\ell_f,\mathbf v)\in I\},\qquad
\mathcal N:=\{(\ell_t,\mathbf v)\in I\}.
\end{aligned}
\tag{1.2}
$$

Let $(S_i)_{i\ge0}$ be the execution, frozen after termination, and set

$$
\mathcal F_i:=\sigma(S_0,\ldots,S_i),
\qquad
T:=\inf\{i\ge0:S_i\notin\mathcal D\},
\qquad
\tau_f:=\inf\{i\ge0:S_i\in\mathcal B\},
\qquad
\inf\varnothing:=\infty.
\tag{1.3}
$$

No termination assumption is imposed. For $n\in\mathbb N_0$, distinguish

$$
\begin{aligned}
\mathrm{vpf}(s_0)&:=\Pr_{s_0}(\tau_f<\infty),\\
F_n(s_0)&:=\Pr_{s_0}(\tau_f\le n),\\
J_n(s_0)&:=\Pr_{s_0}(n<\tau_f<\infty),\\
\mathrm{vpf}(s_0)&=F_n(s_0)+J_n(s_0).
\end{aligned}
\tag{1.4}
$$

Here $J_n$ is the probability of a failure occurring after step $n$; it is neither a conditional probability nor the total runtime tail $\Pr(T>n)$.

### 1.2 Markov Certificate Lemma

Let $\Theta:I\to[0,\infty)$ be finite-valued and measurable, with

$$
\Theta=1\quad\text{on }\mathcal B,
\qquad
\Theta=0\quad\text{on }\mathcal N.
\tag{1.5}
$$

Suppose

$$
\mathbb E_s[\Theta(S')]\le\Theta(s)
\qquad(s\in\mathcal D).
\tag{1.6}
$$

Then

$$
\boxed{
\mathrm{vpf}(s_0)\le\min\{1,\Theta(s_0)\}.
}
\tag{1.7}
$$

**Proof.** Set $Y_i:=\Theta(S_i)$. The one-step condition and absorbing boundaries give

$$
\mathbb E[Y_{i+1}\mid\mathcal F_i]\le Y_i,
\qquad
\mathbb E[Y_n]\le\Theta(s_0)<\infty.
\tag{1.8}
$$

Since $\{\tau_f\le n\}\subseteq\{Y_n\ge1\}$, Markov's inequality[^markov] yields

$$
F_n(s_0)
\le\Pr(Y_n\ge1)
\le\mathbb E[Y_n]
\le\Theta(s_0).
\tag{1.9}
$$

Taking $n\to\infty$ proves Eq. (1.7), because $\{\tau_f\le n\}\uparrow\{\tau_f<\infty\}$.

### 1.3 Strict Contraction and Late Failure

Suppose the stronger condition holds for a uniform $q\in(0,1)$:

$$
\mathbb E_s[\Theta(S')]\le q\Theta(s)
\qquad(s\in\mathcal D).
\tag{1.10}
$$

Then

$$
M_i:=q^{-(i\wedge T)}\Theta(S_{i\wedge T}),
\qquad
\mathbb E[M_{i+1}\mid\mathcal F_i]\le M_i,
\qquad
\mathbb E[M_i]\le\Theta(s_0).
\tag{1.11}
$$

On $\{\tau_f\le m\}$, $T=\tau_f$ and $\Theta(S_T)=1$. Hence

$$
\mathbb E_{s_0}[q^{-\tau_f};\,\tau_f\le m]
\le\mathbb E[M_m]
\le\Theta(s_0)
\quad\Longrightarrow\quad
\mathbb E_{s_0}[q^{-\tau_f};\,\tau_f<\infty]
\le\Theta(s_0).
\tag{1.12}
$$

The restricted expectation does not evaluate $q^{-\tau_f}$ on nonfailure paths. Therefore

$$
\boxed{
\begin{aligned}
J_n(s_0)&\le\min\{1,\Theta(s_0)q^{n+1}\},\\
\Pr_{s_0}(\tau_f=n)&\le\min\{1,\Theta(s_0)q^n\}.
\end{aligned}
}
\tag{1.13}
$$

Strict contraction applies before termination. Failure states retain value $1$, so Eq. (1.13) does not give a decaying bound for the cumulative probability $F_n$.

### 1.4 Signed Power Templates

Let $\eta_\ell(\mathbf v)>0$ be finite-valued and measurable. For a sign $\sigma\in\{+1,-1\}$, exponent $k>0$, and location offsets $b_\ell\in\mathbb R$, define

$$
\Theta^{\sigma}_{k,b}(\ell,\mathbf v)=
\begin{cases}
0,&\ell=\ell_t,\\
1,&\ell=\ell_f,\\
e^{b_\ell}\eta_\ell(\mathbf v)^{\sigma k},
&\ell\notin\{\ell_t,\ell_f\}.
\end{cases}
\tag{1.14}
$$

For an enabled transition $\tau$ from $\ell$, let $p_f^\tau:=\sum_{j:\ell_j=\ell_f}p_j$. The exact one-step condition $\mathbb E_s[\Theta^\sigma_{k,b}(S')]\le q\Theta^\sigma_{k,b}(s)$ is

$$
\boxed{
p_f^\tau e^{-b_\ell}\eta_\ell(\mathbf v)^{-\sigma k}
+
\sum_{j:\ell_j\notin\{\ell_t,\ell_f\}}
p_j e^{b_{\ell_j}-b_\ell}
\mathbb E_{\mathbf r}\!\left[
\left(
\frac{\eta_{\ell_j}(\mathrm{upd}_j(\mathbf v,\mathbf r))}
{\eta_\ell(\mathbf v)}
\right)^{\sigma k}
\right]
\le q.
}
\tag{1.15}
$$

Use $q=1$ for Eq. (1.7), or $0<q<1$ for Eq. (1.13). The failure term is essential; normal termination contributes zero.

In Sections 2–3, assume $s_0\in\mathcal D$ and use a raw function $\eta:I\to(0,\infty)$, with

$$
\eta_0:=\eta(s_0),\qquad
\eta:=\eta(s),\qquad
\eta':=\eta(S'),\qquad
R:=\frac{\eta'}{\eta}.
\tag{1.16}
$$

These sections use a common normalization. Their full moment conditions include both kinds of terminal successor. Arbitrary location offsets must remain in Eq. (1.15) or be absorbed into the function whose moments are certified.

## 2. Positive-Power Certificates: $0<c<1$

### 2.1 Boundary Condition and Violation Bound

Assume

$$
\eta\ge H\quad\text{on }\mathcal B,
\qquad H>0.
\tag{2.1}
$$

For $k>0$, define the raw potential and its terminal values by

$$
U_k^+(s):=\left(\frac{\eta(s)}H\right)^k,
\qquad
\Theta_k^+(s)=
\begin{cases}
U_k^+(s),&s\in\mathcal D,\\
1,&s\in\mathcal B,\\
0,&s\in\mathcal N.
\end{cases}
\tag{2.2}
$$

For $s\in\mathcal D$, the exact one-step factor is

$$
\begin{aligned}
m_+(k,s)
&:=\frac{\mathbb E_s[\Theta_k^+(S')]}{\Theta_k^+(s)}\\
&=\mathbb E_s[R^k\mathbf1_{\{S'\in\mathcal D\}}]
+\left(\frac H\eta\right)^k\Pr_s(S'\in\mathcal B),\\
\rho_+(k)&:=\sup_{s\in\mathcal D}m_+(k,s).
\end{aligned}
\tag{2.3}
$$

A certified $\rho_+(k)\le q_k\le1$, with $q_k>0$, gives

$$
\boxed{
\begin{aligned}
\mathrm{vpf}(s_0)
&\le\min\left\{1,\left(\frac{\eta_0}H\right)^k\right\},\\
J_n(s_0)
&\le\min\left\{1,\left(\frac{\eta_0}H\right)^kq_k^{n+1}\right\}
\qquad(q_k<1).
\end{aligned}
}
\tag{2.4}
$$

The boundary condition implies $\Theta_k^+\le U_k^+$, with equality on $\mathcal D$.

### 2.2 Certification from First-Moment Contraction

A sufficient condition is

$$
\mathbb E_s[\eta']\le c\eta,
\qquad 0<c<1,
\qquad s\in\mathcal D.
\tag{2.5}
$$

For $0<k\le1$, Jensen's inequality gives

$$
m_+(k,s)
\le\mathbb E_s[R^k]
\le\bigl(\mathbb E_s[R]\bigr)^k
\le c^k<1.
\tag{2.6}
$$

Thus $q_k=c^k$ is valid. In particular,

$$
\boxed{
\begin{aligned}
\mathrm{vpf}(s_0)
&\le\min\left\{1,\frac{\eta_0}H\right\},\\
J_n(s_0)
&\le\min\left\{1,\frac{\eta_0}Hc^{n+1}\right\}.
\end{aligned}
}
\tag{2.7}
$$

Within this Jensen family, $k=1$ gives the tightest clipped bounds. For $k>1$, certify $\rho_+(k)$ or the full moment $\mathbb E_s[R^k]$ separately.

### 2.3 Comparison with RepRSM–Hoeffding Bounds

Fix the same raw function $\eta$ and let

$$
Z(s):=\log\frac{\eta(s)}H,
\qquad
Z_0:=Z(s_0)<0,
\qquad
D_s:=Z(S')-Z(s)=\log R.
\tag{2.8}
$$

The failure boundary satisfies $Z\ge0$. The exact coefficient in Eq. (2.3) uses terminal certificate value $1$, equivalently terminal logarithm $0$; using the raw terminal $Z\ge0$ instead gives only a sufficient upper bound.

Define

$$
\begin{aligned}
\Lambda(k)&:=\log\rho_+(k),\qquad \log0:=-\infty,\\
\mathcal K_+&:=\{k>0:\rho_+(k)\le1\},\\
B_{\mathrm{MC}}(Z)
&:=\min\left\{1,\inf_{k\in\mathcal K_+}e^{kZ_0}\right\},
\qquad \inf\varnothing:=+\infty.
\end{aligned}
\tag{2.9}
$$

For the comparison, assume uniformly over $s\in\mathcal D$ that

$$
D_s\in[A,B]\quad\text{almost surely},
\qquad
\mathbb E_s[D_s]\le-\epsilon,
\qquad
\epsilon>0,\quad
\Delta:=B-A>0.
\tag{2.10}
$$

The increment includes branch selection and random updates. Under Eq. (2.5), Jensen gives $\mathbb E_s[D_s]\le\log c$, so $\epsilon=-\log c$ is admissible whenever the bounded-increment assumption holds.

Hoeffding's lemma[^reprsm] gives

$$
\begin{aligned}
m_+(k,s)
&\le\mathbb E_s[e^{kD_s}]\\
&\le\exp\left(-k\epsilon+\frac{k^2\Delta^2}{8}\right)
=e^{-\lambda_H(k)},\\
\lambda_H(k)&:=k\epsilon-\frac{k^2\Delta^2}{8}.
\end{aligned}
\tag{2.11}
$$

Consequently,

$$
k_H:=\frac{8\epsilon}{\Delta^2}
\quad\text{satisfies}\quad
\rho_+(k_H)\le1,
\qquad
B_H(Z):=e^{k_HZ_0}.
\tag{2.12}
$$

This is the RepRSM–Hoeffding bound for the fixed certificate $Z$.[^reprsm] Since $k_H\in\mathcal K_+$,

$$
\boxed{
\mathrm{vpf}(s_0)
\le B_{\mathrm{MC}}(Z)
\le B_H(Z).
}
\tag{2.13}
$$

Equivalently, with $k_*:=\sup(\{0\}\cup\mathcal K_+)$ and $e^{-\infty}:=0$,

$$
B_{\mathrm{MC}}(Z)=e^{k_*Z_0},
\qquad
B_{\mathrm{MC}}(Z)<B_H(Z)
\quad\Longleftrightarrow\quad
k_*>k_H.
\tag{2.14}
$$

A sufficient strict-improvement test is $\Lambda(k_H)<0$. The effective increment on a failure branch is $-Z(s)\le D_s\le B$, so for $\delta>0$,

$$
\Lambda(k_H+\delta)
\le\Lambda(k_H)+B\delta.
\tag{2.15}
$$

Some $\delta>0$ therefore remains feasible, yielding

$$
\boxed{
\Lambda(k_H)<0
\quad\Longrightarrow\quad
B_{\mathrm{MC}}(Z)<B_H(Z)
\qquad(Z_0<0).
}
\tag{2.16}
$$

The comparison fixes $Z$ and improves its Hoeffding relaxation; it does not compare optimization over different certificate families.

## 3. Reciprocal-Power Certificates: $c>1$

### 3.1 Boundary Condition and Violation Bound

Assume

$$
0<\eta\le h\quad\text{on }\mathcal B,
\qquad h>0.
\tag{3.1}
$$

For $k>0$, define

$$
U_k^-(s):=\left(\frac h{\eta(s)}\right)^k,
\qquad
\Theta_k^-(s)=
\begin{cases}
U_k^-(s),&s\in\mathcal D,\\
1,&s\in\mathcal B,\\
0,&s\in\mathcal N.
\end{cases}
\tag{3.2}
$$

The exact one-step factor is

$$
\begin{aligned}
m_-(k,s)
&:=\frac{\mathbb E_s[\Theta_k^-(S')]}{\Theta_k^-(s)}\\
&=\mathbb E_s[R^{-k}\mathbf1_{\{S'\in\mathcal D\}}]
+\left(\frac\eta h\right)^k\Pr_s(S'\in\mathcal B),\\
\rho_-(k)&:=\sup_{s\in\mathcal D}m_-(k,s).
\end{aligned}
\tag{3.3}
$$

A certified $\rho_-(k)\le q_k\le1$, with $q_k>0$, gives

$$
\boxed{
\begin{aligned}
\mathrm{vpf}(s_0)
&\le\min\left\{1,\left(\frac h{\eta_0}\right)^k\right\},\\
J_n(s_0)
&\le\min\left\{1,\left(\frac h{\eta_0}\right)^kq_k^{n+1}\right\}
\qquad(q_k<1).
\end{aligned}
}
\tag{3.4}
$$

Only the failure set requires $\eta\le h$; $\eta$ may be unbounded on $\mathcal D$. The boundary implies $\Theta_k^-\le U_k^-$, so a full negative-moment bound is sufficient. The general construction does not require $c>1$; mean growth is used only in the following sufficient certification.

### 3.2 Certification from Low-Order Moments

Mean growth alone does not imply negative-moment contraction. For example,

$$
\Pr(R=1/2)=\Pr(R=2)=\frac12
\quad\Longrightarrow\quad
\mathbb E[R]=\frac54>1,
\qquad
\mathbb E[R^{-k}]
=\frac{2^k+2^{-k}}2>1
\quad(k>0).
\tag{3.5}
$$

Assume instead finite uniform constants satisfying

$$
\boxed{
\mathbb E_s[R]\ge c>1,
\qquad
\mathbb E_s[R^2]\le D,
\qquad
R\ge r_0>0\quad\text{almost surely},
\qquad
0<r_0<c,\quad D\ge c^2.
}
\tag{3.6}
$$

These full moment and support conditions include all terminal successors. Define

$$
\boxed{
p_*:=\frac{D-c^2}{D-2r_0c+r_0^2},
\qquad
z_*:=\frac{D-r_0c}{c-r_0}.
}
\tag{3.7}
$$

Then $0\le p_*<1$, $z_*\ge c>r_0$, and

$$
R_*=
\begin{cases}
r_0,&\text{with probability }p_*,\\
z_*,&\text{with probability }1-p_*,
\end{cases}
\qquad
\mathbb E[R_*]=c,\quad
\mathbb E[R_*^2]=D.
\tag{3.8}
$$

For every $k>0$,

$$
\boxed{
\mathbb E_s[R^{-k}]
\le q_{\mathrm{mom}}(k)
:=p_*r_0^{-k}+(1-p_*)z_*^{-k}.
}
\tag{3.9}
$$

### 3.3 Proof and Optimality of the Moment Bound

Let $f(r)=r^{-k}$ and let $Q$ be the quadratic satisfying

$$
Q(r_0)=f(r_0),
\qquad
Q(z_*)=f(z_*),
\qquad
Q'(z_*)=f'(z_*).
\tag{3.10}
$$

Since $f'''<0$, the Hermite remainder[^hermite] gives

$$
f(r)-Q(r)
=\frac{f'''(\xi)}6(r-r_0)(r-z_*)^2
\le0
\qquad(r\ge r_0).
\tag{3.11}
$$

Here $\xi$ lies in the interval spanned by $r,r_0,z_*$; equality at the interpolation nodes is immediate. Write

$$
\begin{aligned}
Q(r)&=f(z_*)+f'(z_*)(r-z_*)+A_2(r-z_*)^2\\
&=A_2r^2+A_1r+A_0,\\
A_2&=
\frac{f(r_0)-f(z_*)-f'(z_*)(r_0-z_*)}{(r_0-z_*)^2}>0,\\
A_1&=f'(z_*)-2A_2z_*<0.
\end{aligned}
\tag{3.12}
$$

Therefore,

$$
\begin{aligned}
\mathbb E_s[R^{-k}]
&\le\mathbb E_s[Q(R)]\\
&=A_2\mathbb E_s[R^2]+A_1\mathbb E_s[R]+A_0\\
&\le A_2D+A_1c+A_0\\
&=\mathbb E[Q(R_*)]
=\mathbb E[R_*^{-k}]
=q_{\mathrm{mom}}(k).
\end{aligned}
\tag{3.13}
$$

The feasible distribution $R_*$ attains the bound, so it is sharp under Eq. (3.6). The assertion-specific factor can be smaller:

$$
\rho_-(k)
\le\sup_{s\in\mathcal D}\mathbb E_s[R^{-k}]
\le q_{\mathrm{mom}}(k).
\tag{3.14}
$$

### 3.4 Certificate Selection

Define the parameter sets

$$
\mathcal K_{\mathrm{mom}}^{\le}
:=\{k>0:q_{\mathrm{mom}}(k)\le1\},
\qquad
\mathcal K_{\mathrm{mom}}^{<}
:=\{k>0:q_{\mathrm{mom}}(k)<1\}.
\tag{3.15}
$$

With $\inf\varnothing:=+\infty$, Eqs. (1.7) and (1.13) yield

$$
\boxed{
\begin{aligned}
\mathrm{vpf}(s_0)
&\le
\min\left\{
1,\inf_{k\in\mathcal K_{\mathrm{mom}}^{\le}}
\left(\frac h{\eta_0}\right)^k
\right\},\\
J_n(s_0)
&\le
\min\left\{
1,\inf_{k\in\mathcal K_{\mathrm{mom}}^{<}}
\left(\frac h{\eta_0}\right)^k
q_{\mathrm{mom}}(k)^{n+1}
\right\}.
\end{aligned}
}
\tag{3.16}
$$

An empty moment-certified set does not rule out a direct certificate for $\rho_-(k)$. If $D=c^2$, then $R=c$ almost surely and $q_{\mathrm{mom}}(k)=c^{-k}<1$.

[^markov]: T. Leighton and R. Rubinfeld, *Large Deviations*, Theorem 1. [Lecture notes](https://people.csail.mit.edu/ronitt/COURSE/S07/lec25.pdf).
[^reprsm]: J. Wang, Y. Sun, H. Fu, K. Chatterjee, and A. K. Goharshady, *Quantitative Analysis of Assertion Violations in Probabilistic Programs*, PLDI 2021, §5.1. [Author preprint](https://arxiv.org/html/2011.14617v2).
[^hermite]: *Interpolation and Approximation*, Theorem 6.17. [Lecture notes](https://math.iit.edu/~fass/578_ch6.pdf#page=26).

