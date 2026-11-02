# Tail Bounds via Contractive Potentials and Markov's Inequality

## 1. Program Semantics and a General Tail Bound

### 1.1 Model and Notation

Consider the probabilistic loop

$$
\texttt{while }G(\mathbf x)\texttt{ do }
\mathbf x:=F(\mathbf x,\mathbf r).
$$

Assume measurable guards and transitions. The complete state determines the conditional distribution of the next sample given the execution history. Let $I$ contain the deterministic initial state $\mathbf x_0$ and be closed under guarded transitions almost surely. Write $\mathcal D:=I\cap G$; all one-step conditions below hold at every $\mathbf x\in \mathcal D$.

The state process freezes after exit:

$$
\mathbf X_0=\mathbf x_0,
\qquad
\mathbf X_{i+1}=
\begin{cases}
F(\mathbf X_i,\mathbf r_i),&G(\mathbf X_i),\\
\mathbf X_i,&\neg G(\mathbf X_i).
\end{cases}
\tag{1.1}
$$

Define

$$
T:=\inf\{i\ge0:\neg G(\mathbf X_i)\},
\qquad \inf\varnothing:=\infty,
\qquad
\mathcal F_i:=\sigma(\mathbf X_0,\ldots,\mathbf X_i).
\tag{1.2}
$$

Thus $\{T>n\}=\{G(\mathbf X_n)\}$ for $n\in\mathbb N_0$. No termination assumption is imposed.

### 1.2 Contractive-Potential Lemma

Let $V:I\to[0,\infty)$ be finite-valued and measurable, with

$$
V(\mathbf x)\ge1\quad(\mathbf x\in \mathcal D),
\qquad
V(\mathbf x)=0\quad(\mathbf x\in I\setminus \mathcal D).
\tag{1.3}
$$

Suppose a state-independent $q\in(0,1)$ satisfies

$$
\mathbb E[V(F(\mathbf x,\mathbf r))\mid\mathbf x]
\le qV(\mathbf x)
\qquad(\mathbf x\in \mathcal D).
\tag{1.4}
$$

Then

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le\min\{1,V(\mathbf x_0)q^n\}
\qquad(n\in\mathbb N_0).
}
\tag{1.5}
$$

**Proof.** Set $Y_i:=V(\mathbf X_i)$. By Eq. (1.4) before exit and $Y_i=0$ after exit,

$$
\mathbb E[Y_{i+1}\mid\mathcal F_i]
\le qY_i.
\tag{1.6}
$$

The tower property and induction give

$$
\mathbb E[Y_n]
\le q^nV(\mathbf x_0)<\infty
\qquad(n\in\mathbb N_0).
\tag{1.7}
$$

Since $\{T>n\}=\{Y_n\ge1\}$, Markov's inequality[^markov] yields

$$
\Pr_{\mathbf x_0}(T>n)
=\Pr(Y_n\ge1)
\le\mathbb E[Y_n]
\le V(\mathbf x_0)q^n.
\tag{1.8}
$$

The bound also implies $\Pr_{\mathbf x_0}(T<\infty)=1$. If $\mathbf x_0\notin G$, then $T=0$ and the tail is zero.

In Sections 2–4, assume $\mathbf x_0\in \mathcal D$. Let $\eta:I\to\mathbb R$ be finite-valued and measurable, and write

$$
\eta_0:=\eta(\mathbf x_0),
\qquad \mathbf x':=F(\mathbf x,\mathbf r),
\qquad \eta:=\eta(\mathbf x),
\qquad \eta':=\eta(\mathbf x'),
\qquad R:=\frac{\eta'}{\eta}.
$$

Sections 2 and 3 impose separate assumptions on $\eta$. Both require $\eta>0$ on $\mathcal D$, so $R$ is defined for every guarded transition.

## 2. Positive-Power Potentials

### 2.1 Moment Condition and Tail Bound

Assume

$$
\eta\ge0\text{ on }I,
\qquad
\eta\ge a\text{ on }\mathcal D,
\qquad a>0.
\tag{2.1}
$$

For $k>0$, define

$$
V_k^+(\mathbf x)=
\begin{cases}
\left(\dfrac{\eta(\mathbf x)}a\right)^k,&\mathbf x\in \mathcal D,\\[2mm]
0,&\mathbf x\in I\setminus \mathcal D,
\end{cases}
\tag{2.2}
$$

and

$$
\rho_+(k):=
\sup_{\mathbf x\in \mathcal D}
\mathbb E\!\left[
R^k\mathbf1_{\{G(\mathbf x')\}}
\mid\mathbf x
\right].
\tag{2.3}
$$

If $\rho_+(k)\le q_k$ for a certified $q_k\in(0,1)$, then

$$
\begin{aligned}
\mathbb E[V_k^+(\mathbf x')\mid\mathbf x]
&=V_k^+(\mathbf x)
\mathbb E\!\left[
R^k\mathbf1_{\{G(\mathbf x')\}}
\mid\mathbf x
\right]\\
&\le q_kV_k^+(\mathbf x).
\end{aligned}
\tag{2.4}
$$

Applying Eq. (1.5),

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le\min\left\{
1,\left(\frac{\eta_0}a\right)^kq_k^n
\right\}.
}
\tag{2.5}
$$

### 2.2 Certification from First-Moment Contraction

A sufficient condition is

$$
\mathbb E[\eta'\mid\mathbf x]\le c\eta,
\qquad 0<c<1.
\tag{2.6}
$$

For $0<k\le1$, nonnegativity and Jensen's inequality give

$$
\mathbb E\!\left[R^k\mathbf1_{\{G(\mathbf x')\}}\mid\mathbf x\right]
\le\mathbb E[R^k\mid\mathbf x]
\le\bigl(\mathbb E[R\mid\mathbf x]\bigr)^k
\le c^k<1.
\tag{2.7}
$$

Thus $q_k=c^k$ is valid. In particular, $k=1$ yields

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le\min\left\{1,\frac{\eta_0}a c^n\right\}.
}
\tag{2.8}
$$

For $k>1$, bound $\rho_+(k)$ directly or certify $\mathbb E[R^k\mid\mathbf x]\le q_k<1$.

## 3. Reciprocal-Power Potentials

### 3.1 Moment Condition and Tail Bound

Assume

$$
0<\eta\le b\text{ on }\mathcal D,
\qquad b>0.
\tag{3.1}
$$

For $k>0$, define

$$
V_k^-(\mathbf x)=
\begin{cases}
\left(\dfrac b{\eta(\mathbf x)}\right)^k,&\mathbf x\in \mathcal D,\\[2mm]
0,&\mathbf x\in I\setminus \mathcal D,
\end{cases}
\tag{3.2}
$$

and

$$
\rho_-(k):=
\sup_{\mathbf x\in \mathcal D}
\mathbb E\!\left[
R^{-k}\mathbf1_{\{G(\mathbf x')\}}
\mid\mathbf x
\right].
\tag{3.3}
$$

The integrand equals $R^{-k}$ on nonterminal successors and is defined as zero otherwise; terminal reciprocals are never evaluated.

If $\rho_-(k)\le q_k$ for a certified $q_k\in(0,1)$, then

$$
\begin{aligned}
\mathbb E[V_k^-(\mathbf x')\mid\mathbf x]
&=V_k^-(\mathbf x)
\mathbb E\!\left[
R^{-k}\mathbf1_{\{G(\mathbf x')\}}
\mid\mathbf x
\right]\\
&\le q_kV_k^-(\mathbf x).
\end{aligned}
\tag{3.4}
$$

Applying Eq. (1.5),

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le\min\left\{
1,\left(\frac b{\eta_0}\right)^kq_k^n
\right\}.
}
\tag{3.5}
$$

### 3.2 Certification from Low-Order Moments

Assume finite, state-independent constants satisfying

$$
\boxed{
\mathbb E[R\mid\mathbf x]\ge c>1,
\qquad
\mathbb E[R^2\mid\mathbf x]\le D,
\qquad
R\ge r_0>0\quad\text{almost surely},
}
\tag{3.6}
$$

where $0<r_0<c$ and $D\ge c^2$. Equivalently,

$$
\mathbb E[\eta'\mid\mathbf x]\ge c\eta,
\qquad
\mathbb E[(\eta')^2\mid\mathbf x]\le D\eta^2,
\qquad
\eta'\ge r_0\eta\quad\text{almost surely}.
\tag{3.7}
$$

These conditions include terminating successors. The support bound ensures finite negative moments; mean growth alone does not certify their contraction.

Define

$$
\boxed{
p_*:=\frac{D-c^2}{D-2r_0c+r_0^2},
\qquad
z_*:=\frac{D-r_0c}{c-r_0}.
}
\tag{3.8}
$$

Then $0\le p_*<1$ and $z_*\ge c>r_0$. The two-point variable

$$
R_*=
\begin{cases}
r_0,&\text{with probability }p_*,\\
z_*,&\text{with probability }1-p_*
\end{cases}
\tag{3.9}
$$

satisfies

$$
\mathbb E[R_*]=c,
\qquad
\mathbb E[R_*^2]=D.
\tag{3.10}
$$

For every $k>0$,

$$
\boxed{
\mathbb E[R^{-k}\mid\mathbf x]
\le q_{\mathrm{mom}}(k)
:=p_*r_0^{-k}+(1-p_*)z_*^{-k}.
}
\tag{3.11}
$$

### 3.3 Proof and Optimality of the Moment Bound

Fix $k>0$, let $f(r)=r^{-k}$, and choose a quadratic $Q$ satisfying

$$
Q(r_0)=f(r_0),
\qquad Q(z_*)=f(z_*),
\qquad Q'(z_*)=f'(z_*).
\tag{3.12}
$$

The Hermite remainder[^hermite] gives, for $r\ge r_0$,

$$
\begin{aligned}
f'''(r)&=-k(k+1)(k+2)r^{-k-3}<0,\\
f(r)-Q(r)&=\frac{f'''(\xi)}6(r-r_0)(r-z_*)^2\le0.
\end{aligned}
\tag{3.13}
$$

Here $\xi$ lies in the interval spanned by $r,r_0,z_*$; equality at the interpolation nodes is immediate. Write

$$
\begin{aligned}
Q(r)&=f(z_*)+f'(z_*)(r-z_*)+A(r-z_*)^2,\\[1mm]
A&=\frac{f(r_0)-f(z_*)-f'(z_*)(r_0-z_*)}{(r_0-z_*)^2}>0.
\end{aligned}
\tag{3.14}
$$

Strict convexity gives $A>0$. Expanding $Q(r)=Ar^2+Br+C$ yields

$$
B=f'(z_*)-2Az_*<0.
\tag{3.15}
$$

Therefore,

$$
\begin{aligned}
\mathbb E[R^{-k}\mid\mathbf x]
&\le\mathbb E[Q(R)\mid\mathbf x]\\
&=A\mathbb E[R^2\mid\mathbf x]+B\mathbb E[R\mid\mathbf x]+C\\
&\le AD+Bc+C\\
&=\mathbb E[Q(R_*)]
=\mathbb E[R_*^{-k}]
=q_{\mathrm{mom}}(k).
\end{aligned}
\tag{3.16}
$$

The feasible distribution $R_*$ attains the bound, so it is sharp under Eq. (3.6). Adding $\mathbb E[R\mid\mathbf x]\le c''$ with $c''\ge c$ leaves it unchanged. The program-specific coefficient satisfies

$$
\rho_-(k)
\le\sup_{\mathbf x\in \mathcal D}\mathbb E[R^{-k}\mid\mathbf x]
\le q_{\mathrm{mom}}(k),
\tag{3.17}
$$

and either inequality may be strict.

### 3.4 Tail Bound from the Moment Certificate

The moment conditions do not guarantee $q_{\mathrm{mom}}(k)<1$. Define

$$
\mathcal K_{\mathrm{mom}}
:=\{k>0:q_{\mathrm{mom}}(k)<1\}.
\tag{3.18}
$$

For each $k\in\mathcal K_{\mathrm{mom}}$, Eq. (3.5) gives

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le\min\left\{
1,\left(\frac b{\eta_0}\right)^kq_{\mathrm{mom}}(k)^n
\right\}.
}
\tag{3.19}
$$

If $\mathcal K_{\mathrm{mom}}=\varnothing$, direct certification of $\rho_-(k)<1$ may still succeed. If $D=c^2$, then $R=c$ almost surely, $p_*=0$, $z_*=c$, and $q_{\mathrm{mom}}(k)=c^{-k}<1$.

## 4. Parameter Optimization

Fix $\eta$, its threshold, and any moment constants. For either family, write $V_k$ for its potential and let $\mathcal C$ be a nonempty set of certified pairs $(k,q)$ with $k>0$, $0<q<1$, satisfying Eq. (1.4) with $V=V_k$. Then

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le\min\left\{
1,\inf_{(k,q)\in\mathcal C}V_k(\mathbf x_0)q^n
\right\}.
}
\tag{4.1}
$$

For fixed $n$, minimize

$$
\log V_k(\mathbf x_0)+n\log q
=
\begin{cases}
k\log(\eta_0/a)+n\log q,&\text{positive power},\\[1mm]
k\log(b/\eta_0)+n\log q,&\text{reciprocal power}.
\end{cases}
\tag{4.2}
$$

The moment certificate uses $\mathcal C=\{(k,q_{\mathrm{mom}}(k)):k\in\mathcal K_{\mathrm{mom}}\}$ when nonempty. With only the Jensen choice $q=c^k$, $0<k\le1$, $k=1$ already minimizes the clipped positive-power bound.

[^markov]: [Leighton and Rubinfeld, *Large Deviations*, Theorem 1](https://people.csail.mit.edu/ronitt/COURSE/S07/lec25.pdf).
[^hermite]: [*Interpolation and Approximation*, Theorem 6.17](https://math.iit.edu/~fass/578_ch6.pdf#page=26).
