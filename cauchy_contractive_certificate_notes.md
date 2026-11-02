# 基于 Cauchy 的非整数幂收缩证书合成

## 1. 问题描述与 Cauchy–Schwarz 不等式

### 1.1 分析目标

考虑概率循环

$$
\texttt{while }G(\mathbf x)\texttt{ do }\mathbf x:=F(\mathbf x,\mathbf r),
$$

其中 $\mathbf r$ 表示一次迭代中的随机采样。设 $I$ 是已认证的不变量，证明域为

$$
D(\mathbf x):=I(\mathbf x)\land G(\mathbf x),
$$

终止时间定义为

$$
T:=\inf\{i\ge0:\neg G(\mathbf X_i)\},
$$

程序不终止时令 $T=\infty$。本文考虑 $\mathbf x_0\in D$；若初态已经不满足守卫，则 $T=0$。

目标是寻找多项式 $\eta$、指数 $k>0$ 和收缩率 $0<\rho<1$，满足

$$
\eta(\mathbf x)\ge a_0>0\quad(\mathbf x\in D),
\qquad
\eta(F(\mathbf x,\mathbf r))\ge0
$$

以及

$$
\boxed{
\mathbb E\!\left[
\left(\frac{\eta'}{\eta}\right)^k
\middle|\mathbf x
\right]\le\rho,
\qquad \mathbf x\in D,
}
\tag{1}
$$

其中 $\eta'=\eta(F(\mathbf x,\mathbf r))$。后继非负性必须覆盖随机分布的支持，包括一步后退出循环的状态。

由此可以得到

$$
\boxed{
\Pr_{\mathbf x_0}(T>n)
\le
\min\left\{1,
\left(\frac{\eta(\mathbf x_0)}{a_0}\right)^k\rho^n
\right\}.
}
\tag{2}
$$

对应模板为

$$
\Phi_n(\mathbf x,i)
=
\left(\frac{\eta(\mathbf x)}{a_0}\right)^k\rho^{n-i}
=
\exp\!\left(k\log\frac{\eta(\mathbf x)}{a_0}-\ell(n-i)\right),
\qquad \ell=-\log\rho.
$$

幂形式允许后继 $\eta'=0$，此时取 $0^k=0$；对数表达式只用于正值处。下文主要归一化为 $a_0=1$。这里的 $\rho$ 是所选 $k$ 的矩收缩率，应与已有一阶收缩条件中的 $c$ 区分。

### 1.2 Cauchy–Schwarz 不等式

对任意实向量 $\mathbf q,\mathbf b\in\mathbb R^s$，

$$
\boxed{
|\mathbf q^\top\mathbf b|
\le\|\mathbf q\|_2\|\mathbf b\|_2
=
\left(\sum_jq_j^2\right)^{1/2}
\left(\sum_jb_j^2\right)^{1/2}.
}
\tag{3}
$$

由于两边非负，对任意实数 $k>0$，

$$
|\mathbf q^\top\mathbf b|^k
\le
\left(\sum_jq_j^2\right)^{k/2}
\left(\sum_jb_j^2\right)^{k/2}.
$$

因此，**Cauchy 分离本身不要求 $k$ 是整数，也不要求随机分量相互独立。**

### 1.3 贯穿样例

考虑以下程序，其中更新 $x$ 时使用旧的 $y$：

```text
while x >= 1 do
    Z := 0  with probability 99/100
         10 with probability  1/100;
    x := x * ((3+y)/10 + (1+y)*Z/20);
    y := Z/10
od
```

不变量取 $x>0,\ 0\le y\le1$，因而

$$
D=\{(x,y):x\ge1,\ 0\le y\le1\}.
$$

记

$$
p_1(y)=\frac{3+y}{10},\qquad
p_2(y)=\frac{1+y}{20},
$$

则 $x'=x(p_1(y)+p_2(y)Z)$。后文分别在固定 $\eta=x$ 和待合成 $\eta_\theta$ 的情况下分析这个程序。

## 2. Cauchy 方法的推导

### 2.1 将后继证书值展开为状态部分与随机部分

对后继证书值作精确展开：

$$
\boxed{
\eta_\theta(F(\mathbf x,\mathbf r))
=
\sum_{j=1}^s q_{j,\theta}(\mathbf x)b_j(\mathbf r)
=
\mathbf q_\theta(\mathbf x)^\top\mathbf b(\mathbf r).
}
\tag{4}
$$

随机基 $b_j$ 预先固定，例如 $1,Z,Z^2$；$q_{j,\theta}$ 必须由证书模板与程序更新展开得到。若将它们另外设为模板，必须加入保证式 (4) 的系数匹配约束。

这里展开的是**分子 $\eta'$**，不要求 $\eta'/\eta$ 具有多项式系数。例如 $\eta=x,\ x'=x/2+Z$ 时，比值中出现 $Z/x$，而分子仍是多项式。

### 2.2 分离条件矩

由 $\eta>0$、$\eta'\ge0$ 和 Cauchy 不等式，

$$
\left(\frac{\eta'}{\eta}\right)^k
\le
\left(
\frac{\sum_jq_{j,\theta}(\mathbf x)^2}{\eta_\theta(\mathbf x)^2}
\right)^{k/2}
\left(\sum_jb_j(\mathbf r)^2\right)^{k/2}.
$$

若随机基向量的条件分布不依赖状态，定义

$$
\Gamma(k):=
\mathbb E\!\left[
\left(\sum_jb_j(\mathbf r)^2\right)^{k/2}
\right]<\infty.
$$

取条件期望得到

$$
\boxed{
\mathbb E\!\left[
\left(\frac{\eta'}{\eta}\right)^k\middle|\mathbf x
\right]
\le
\Gamma(k)
\left(
\frac{\sum_jq_{j,\theta}(\mathbf x)^2}{\eta_\theta(\mathbf x)^2}
\right)^{k/2}.
}
\tag{5}
$$

于是，只需寻找 $B\ge0$，使

$$
\boxed{
D\Longrightarrow
\sum_jq_{j,\theta}^2\le B\eta_\theta^2,
\qquad
\Gamma(k)B^{k/2}\le\rho<1.
}
\tag{6}
$$

若分布依赖状态，需要用 $\Gamma(k,\mathbf x)$ 的统一已认证上界替代 $\Gamma(k)$。随机基函数之间可以相关，但矩计算必须使用正确的联合分布。

固定随机基与证书后，三个量的作用不同：

$$
\underbrace{B}_{\text{状态范数界，不依赖 }k},\qquad
\underbrace{\rho(k,B)=\Gamma(k)B^{k/2}}_{\text{矩收缩率}},\qquad
\underbrace{\beta_n=A^k\rho(k,B)^n}_{\text{尾界}},
\quad A=\frac{\eta(\mathbf x_0)}{a_0}.
$$

**改变 $k$ 可以改善 $\rho$ 和最终尾界，但不会改变同一范数约束中的最优 $B$。** 改变随机基会同时改变 $B$ 和 $\Gamma$，此时不能只比较 $B$。

### 2.3 由收缩条件得到尾界

定义终止后取零的存活过程

$$
Y_i:=\eta(\mathbf X_i)^k\mathbf1_{\{T>i\}}.
$$

由一步收缩与后继非负性，

$$
\mathbb E[Y_{i+1}\mid\mathcal F_i]\le\rho Y_i,
\qquad
\mathbb E[Y_n]\le\rho^n\eta(\mathbf x_0)^k.
$$

另一方面，存活时 $\eta\ge a_0$，故

$$
a_0^k\mathbf1_{\{T>n\}}\le Y_n.
$$

取期望即得到式 (2)。这个证明不需要假设终止后保持最终 $\eta$ 值的停止过程继续严格收缩。

## 3. 固定 $\eta$ 时搜索 $k$

### 3.1 推导：先最小化 $B$，再优化完整尾界

固定 $\eta$、随机基和证明域后，$\mathbf q$ 已确定。需要求解

$$
\min B
\quad\text{s.t.}\quad
D\Longrightarrow
B\eta^2-\sum_jq_j^2\ge0.
\tag{7}
$$

该约束不含 $k$。对任意 $k>0$，较小的 $B$ 都使 Cauchy 上界不增，因此这一阶段可以与指数搜索分离。

记找到并认证的范数上界为 $B_*>0$，令

$$
\rho(k)=\Gamma(k)B_*^{k/2}.
$$

对给定初态和目标时间 $n\ge1$，优化目标为

$$
\boxed{
L_n(k)
=
\log\beta_n(k)
=
k\log A+n\log\Gamma(k)+\frac{nk}{2}\log B_*.
}
\tag{8}
$$

不能只最小化 $\rho(k)$，因为初值前因子 $A^k$ 也随 $k$ 变化。

若 $B_*=0$，则证明域上 $\mathbf q=0$，一步后 $\eta'=0$，结合守卫上的正下界可推出从合法初态出发至多执行一次迭代；此时不使用含 $\log B_*$ 的目标。

### 3.2 求解模板：范数界的 SOS/SDP

将证明域写为

$$
D=\{\mathbf x:g_\ell(\mathbf x)\ge0,\ d_h(\mathbf x)=0\}.
$$

用下列恒等式认证式 (7)：

$$
\boxed{
\begin{array}{ll}
\operatorname{minimize}&B\\[1mm]
\operatorname{subject\ to}&B\ge0,\\[1mm]
&B\eta^2-\sum_jq_j^2
\equiv
\sigma_0+\sum_\ell\sigma_\ell g_\ell+\sum_h\lambda_hd_h,\\[1mm]
&\sigma_\ell\in\mathrm{SOS}.
\end{array}
}
\tag{9}
$$

等式乘子 $\lambda_h$ 为任意多项式。固定乘子次数，令

$$
\sigma_\ell=\mathbf m_\ell^\top Q_\ell\mathbf m_\ell,
\qquad Q_\ell\succeq0,
$$

再逐项匹配多项式系数。由于 $\eta,\mathbf q$ 已固定，所有匹配约束对 $B$、Gram 矩阵和等式乘子系数都是仿射的。这就是标准 SDP；由前端生成系数匹配约束，再使用 CVXPY 建模并交给 MOSEK。[^sos]

固定 $\eta$ 时还须检查 $\eta\ge a_0$ 和后继非负性；它们可以分别用相应证明域上的 SOS 证书认证。状态空间应被全称覆盖，不能仅以有限采样点上的不等式代替这些证明义务。

**固定 $\eta$ 的 $B$ 不需要外层搜索。** 同一个 SDP 不因整数或非整数 $k$ 而改变。

### 3.3 求解模板：指数的一维优化

在预选指数范围 $\mathcal K\subset(0,\infty)$ 内，取收缩裕量 $\varepsilon\in(0,1)$，求解

$$
\boxed{
\min_{k\in\mathcal K}L_n(k)
\quad\text{s.t.}\quad
\log\Gamma(k)+\frac{k}{2}\log B_*
\le\log(1-\varepsilon).
}
\tag{10}
$$

一种实现是整数粗搜，再在有效区域搜索小分母有理数；应同时检查 $0<k<1$，而不是因为整数候选失败就停止搜索。这里细化的是 $k$，不是重新求一个依赖 $k$ 的 $B$。

若随机基范数 $S=\|\mathbf b\|_2$ 有有限个正取值 $s_\ell$，概率为 $\pi_\ell>0$，则

$$
\Gamma(k)=\sum_\ell\pi_\ell s_\ell^k,
$$

$$
\log\rho(k)
=
\operatorname{LSE}_\ell
\left(\log\pi_\ell+k\left[\log s_\ell+\tfrac12\log B_*\right]\right),
$$

其中 $\operatorname{LSE}(v)=\log\sum_\ell e^{v_\ell}$。所以在实数区间 $[k_{\min},k_{\max}]$ 上，式 (10) 是一维凸问题，可通过 log-sum-exp 的指数锥表示求解；之后选择附近有理数并重新认证。[^exp]

若使用的是任意构造的 $\overline\Gamma(k)$ 而非准确矩函数，不应未经检查就假定其对数仍凸；此时可使用标量搜索。最终必须采用经过认证的分布矩上界，而不只是浮点估计。

### 3.4 样例：固定 $\eta(x,y)=x$

由第 1 节程序，选择随机基 $(1,Z)$，得到

$$
q_1=xp_1(y),\qquad q_2=xp_2(y),
\qquad
\Gamma(k)=\frac{99}{100}+\frac1{100}101^{k/2}.
$$

因为 $x\ge1$，可消去范数约束中的 $x^2$：

$$
0\le y\le1
\Longrightarrow
S(y):=p_1(y)^2+p_2(y)^2
=\frac{37+26y+5y^2}{400}\le B.
$$

对应的 SDP 模板为

$$
\min B,
\qquad
B-S(y)
\equiv\sigma_0(y)+y\sigma_1(y)+(1-y)\sigma_2(y),
\quad\sigma_i\in\mathrm{SOS}.
\tag{11}
$$

一个精确最优值是 $B_*=17/100$。上界可由显式证书验证：

$$
\boxed{
\frac{17}{100}-S(y)
=
\frac{31}{400}(1-y)^2
+y\cdot\frac9{100}(1-y)^2
+(1-y)\cdot\frac9{100}y^2.
}
\tag{12}
$$

而 $S(1)=17/100$，说明该范数界不能进一步降低。于是

$$
\boxed{
\rho_C(k)
=
\left(\frac{99}{100}+\frac1{100}101^{k/2}\right)
\left(\frac{17}{100}\right)^{k/2}.
}
\tag{13}
$$

例如，固定有理数 $k=3/2$，由

$$
101^{3/4}<32,
\qquad
\left(\frac{131}{100}\right)^4
\left(\frac{17}{100}\right)^3
<\left(\frac7{20}\right)^4
$$

可认证 $\rho_C(3/2)<7/20$，从而

$$
\Pr(T>n)
\le\min\left\{1,x_0^{3/2}\left(\frac7{20}\right)^n\right\}.
$$

这里 $3/2$ 只是一个有效指数，最优指数仍由 $x_0,n$ 和式 (10) 决定。无论怎样调整 $k$，当前范数问题的最优 $B$ 都仍是 $17/100$。

## 4. 同时搜索 $\eta$ 和 $k$

### 4.1 推导：固定范数参数，保留凸的证书合成内层

设

$$
\eta_\theta(\mathbf x)=\sum_\alpha\theta_\alpha\mathbf x^\alpha,
$$

随机基、程序更新和证明域固定。展开后的 $q_{j,\theta}$ 对 $\theta$ 仿射。

直接联合优化

$$
B\eta_\theta^2-\sum_jq_{j,\theta}^2\ge0
$$

会出现 $B\theta_\alpha\theta_\beta$ 等未知量乘积。因此改为外层固定

$$
t:=\sqrt B>0.
$$

在 $\eta_\theta\ge1$ 时，范数约束等价于

$$
\|\mathbf q_\theta\|_2\le t\eta_\theta
\iff
\boxed{
M_{\theta,t}(\mathbf x):=
\begin{bmatrix}
t\eta_\theta&\mathbf q_\theta^\top\\
\mathbf q_\theta&t\eta_\theta I_s
\end{bmatrix}\succeq0.
}
\tag{14}
$$

等价性可由 Schur 补得到。固定 $t$ 后，矩阵元素对 $\theta$ 仿射。

对于固定 $t,k>0$，收缩率

$$
\rho_t(k)=\Gamma(k)t^k
$$

与 $\theta$ 无关。因此内层只需寻找较小的初值

$$
A(t):=\min\eta_\theta(\mathbf x_0),
$$

其中最小化范围受全部证书约束限制。实际求解时使用找到并认证的可行候选初值，而不直接将数值最优值视为严格证明。

得到候选后，外层比较

$$
\boxed{
\beta_n(t,k)=A(t)^k[\Gamma(k)t^k]^n,
\qquad
L_n(t,k)=k\log A(t)+n\log\Gamma(k)+nk\log t.
}
\tag{15}
$$

**每个固定 $t$ 只需要求一次证书合成 SDP；这一内层不依赖 $k$。**

### 4.2 求解模板：固定 $t$ 的矩阵 SOS/SDP

记 $\mathcal Q_D$ 为使用固定生成元和固定次数的标量 SOS 证书集合：

$$
p\in\mathcal Q_D
\quad\Longleftrightarrow\quad
p\equiv\sigma_0+\sum_\ell\sigma_\ell g_\ell+\sum_h\lambda_hd_h,
\quad\sigma_\ell\in\mathrm{SOS}.
$$

固定 $t$，求解

$$
\boxed{
\begin{array}{ll}
\operatorname{minimize}&\eta_\theta(\mathbf x_0)\\[1mm]
\operatorname{subject\ to}
&\eta_\theta-1\in\mathcal Q_D,\\[1mm]
&\eta_\theta(F_j(\mathbf x))\in\mathcal Q_D
\quad\text{对每个有限随机分支 }j,\\[1mm]
&M_{\theta,t}
\equiv S_0+\sum_\ell g_\ell S_\ell+\sum_h d_hH_h,\\[1mm]
&S_\ell\text{ 为矩阵 SOS},\quad
H_h\text{ 为任意对称多项式矩阵}.
\end{array}
}
\tag{16}
$$

连续随机分布时，后继非负性改在联合域 $D\times\operatorname{Support}(\mathbf r)$ 上认证；若该支持非半代数，需要另外的有效非负性证明或支持过近似。

矩阵 SOS 可以编码为

$$
S_\ell(\mathbf x)
=
(\mathbf m_\ell(\mathbf x)\otimes I_{s+1})^\top
Q_\ell
(\mathbf m_\ell(\mathbf x)\otimes I_{s+1}),
\qquad Q_\ell\succeq0.
$$

也可以将 $\mathbf w^\top S_\ell(\mathbf x)\mathbf w$ 作为标量 SOS。对式 (16) 匹配系数后，未知模板系数、Gram 矩阵和乘子系数均以仿射方式出现，因而形成 SDP；CVXPY 中的半正定约束也要求所建矩阵表达式是仿射的。[^cvx]

使用相同生成元，并让矩阵 SOS 次数足以容纳 $\eta_\theta$ 的正性证书，可保证后文所用的固定次数可行性单调性。

### 4.3 $B$ 的范围：收缩上限与证书可行性下限

#### （a）由分布矩确定上限

固定 $k>0$，严格收缩要求

$$
\Gamma(k)B^{k/2}<1
\iff
\boxed{B< B_{\mathrm{crit}}(k):=\Gamma(k)^{-2/k}.}
\tag{17}
$$

采用收缩裕量 $\rho\le1-\varepsilon$ 后，可以使用

$$
\boxed{
B\le B_{\max}(k,\varepsilon)
:=\left(\frac{1-\varepsilon}{\Gamma(k)}\right)^{2/k}.
}
\tag{18}
$$

若搜索指数集合为 $\mathcal K$，整体范围取

$$
\boxed{
B_{\max}(\mathcal K,\varepsilon)
=
\sup_{k\in\mathcal K}
\left(\frac{1-\varepsilon}{\Gamma(k)}\right)^{2/k}.
}
\tag{19}
$$

这是只涉及分布的标量计算，不需要运行 SOS 求解器。每个候选 $B$ 仍需和实际选择的 $k$ 检查收缩条件。使用已认证上界 $\overline\Gamma$ 替代 $\Gamma$ 时，得到的是相应充分条件所允许的范围。

有限的 $\mathcal K$ 可以逐项计算；连续区间上的上限应通过可靠的全局标量分析确定。**仅在整数上计算出的范围只覆盖这些整数；扩展到其他指数时需要重新计算范围。**

若 $S=\|\mathbf b\|_2$ 有限支持且严格为正，还可以得到允许任意 $k>0$ 时的理论上限。由 Jensen，

$$
\log\Gamma(k)\ge k\mathbb E[\log S],
$$

因此任何严格收缩都必须满足

$$
\boxed{
B<B_{\mathrm{crit,all}}
:=\exp\!\left(-2\mathbb E[\log S]\right).
}
\tag{20}
$$

在这些假设下，若严格小于该值，足够小的正 $k$ 会使 $\Gamma(k)B^{k/2}<1$。但它不保证预设的收缩裕量，也不保证存在满足状态约束的 $\eta$。

#### （b）由可行性二分定位下限

对固定的模板族、随机基、生成元和 SOS 次数，记

$$
\mathcal F(t):=\text{式 (16) 忽略目标函数后的可行性问题},
$$

$$
\underline B_{\mathrm{SOS}}
:=\inf\{t^2:\mathcal F(t)\text{ 可行}\}.
$$

当 $t'\ge t$ 时，

$$
M_{\theta,t'}-M_{\theta,t}
=(t'-t)\eta_\theta I_{s+1}\succeq0.
$$

在前述兼容的 SOS 次数设置下，$\eta_\theta$ 的正性证书也能给出这一差值的矩阵 SOS 证书，所以

$$
\boxed{
\mathcal F(t)\text{ 可行}
\Longrightarrow
\mathcal F(t')\text{ 可行}\quad(t'\ge t).
}
\tag{21}
$$

由此得到如下范围划分，端点 $\underline B_{\mathrm{SOS}}$ 是否可行需单独判断：

| 范围 | 含义 |
| --- | --- |
| $0\le B<\underline B_{\mathrm{SOS}}$ | 当前固定模板与 SOS 编码没有可行证书 |
| $\underline B_{\mathrm{SOS}}<B\le B_{\max}$ | 状态约束可能与收缩条件同时满足的候选区间 |
| $B>B_{\max}$ | 当前 $\mathcal K,\varepsilon$ 与所用矩上界不能认证收缩 |

先令 $t_H=\sqrt{B_{\max}}$，检查 $\mathcal F(t_H)$。若可行，以它作为上端点，从 $t_L=0$ 开始二分；若 $t=0$ 可行，则单独处理一步终止的退化情形。二分更新为

$$
\boxed{
\begin{aligned}
t_M&=(t_L+t_H)/2,\\
\mathcal F(t_M)\text{ 可行}&\Longrightarrow t_H\leftarrow t_M,\\
\mathcal F(t_M)\text{ 被可靠确认为不可行}
&\Longrightarrow t_L\leftarrow t_M.
\end{aligned}
}
\tag{22}
$$

若上端点被可靠确认为不可行，则当前编码下更小的参数也不可行，应调整模板、次数、随机基、指数集合或收缩裕量。

**超时、求解失败或低精度状态不作为不可行剪枝依据。** 浮点求解器状态应与严格可行性证据区分；对于低精度结果，应保留不确定区间或重求。[^status]

#### （c）最小 $B$ 与最小尾界不同

增大 $t$ 放宽约束，可能允许更小的初值 $A(t)$。因此不能仅保留最小 $B$ 对应的证书：

$$
\boxed{
\beta_n(t,k)
=\bigl[A(t)t^n\bigr]^k\Gamma(k)^n.
}
\tag{23}
$$

当随机基和分布固定时，两个候选在相同 $k$ 下的未截断尾界排序由 $A(t)t^n$ 决定。但不同 $t$ 的收缩可行指数集合可能不同，仍须逐个检查 $\rho_t(k)<1$ 或预设裕量。

因此，二分只用来定位最小可行范数界；随后在可行区间中粗搜并局部细化 $t$，比较完整尾界。该尾界目标不保证关于 $t$ 单调，不能用同样的可行性二分直接最小化它。

### 4.4 样例：合成 $\eta$，并确定 $B$ 的具体范围

采用模板族

$$
\eta_\theta(x,y)=\alpha x+\beta,
\qquad\alpha,\beta\ge0,\quad\alpha+\beta=1.
$$

这些条件保证守卫上的 $\eta_\theta\ge1$，并保证本例后继正性。该限制定义了本例的搜索族，不代表所有仿射多项式。

展开得到

$$
q_1=\alpha xp_1(y)+\beta,
\qquad q_2=\alpha xp_2(y).
$$

为复用已有标量证书，在不改变证明域的情况下，可加入非负生成元 $(x-1)y$ 与 $(x-1)(1-y)$。固定 $t$，具体内层模板为

$$
\boxed{
\begin{array}{ll}
\operatorname{minimize}&\alpha x_0+\beta\\[1mm]
\operatorname{subject\ to}&\alpha,\beta\ge0,\quad\alpha+\beta=1,\\[1mm]
&\begin{bmatrix}
t(\alpha x+\beta)&q_1&q_2\\
q_1&t(\alpha x+\beta)&0\\
q_2&0&t(\alpha x+\beta)
\end{bmatrix}\\[4mm]
&\qquad\equiv S_0+(x-1)S_x+yS_y+(1-y)S_u\\
&\qquad\quad +(x-1)yS_{xy}+(x-1)(1-y)S_{xu},\\[1mm]
&S_0,S_x,S_y,S_u,S_{xy},S_{xu}\text{ 为矩阵 SOS}.
\end{array}
}
\tag{24}
$$

对于 $k=2$，

$$
\Gamma(2)=2,\qquad \rho(2,B)=2B,
$$

所以 $B<1/2$。若要求 $\rho\le0.98$，则

$$
\boxed{B\le0.49,\qquad t\le0.7.}
$$

已知候选 $\eta=x$ 满足 $B_0=17/100$，所以寻找最小范数界时可缩小到 $B\in[0,17/100]$。但优化完整尾界时，仍应考虑更大的 $B$，因为它可能允许更小的初值。

这里的已有范数证书在足够的矩阵 SOS 次数下也可用于式 (24)。令 $p=(p_1,p_2)^\top$、$e_0=(1,0,0)^\top$，$t>0$，则

$$
\begin{bmatrix}t&p^\top\\p&tI_2\end{bmatrix}
=
\frac1t
\begin{bmatrix}p^\top\\tI_2\end{bmatrix}
\begin{bmatrix}p&tI_2\end{bmatrix}
+
\frac{t^2-p_1^2-p_2^2}{t}e_0e_0^\top.
$$

结合式 (12)，右边在 $t^2\ge17/100$ 时具有所需证书。再乘以 $x=1+(x-1)$，所得项可由式 (24) 的生成元及其已加入的乘积表示。因此，在次数足够时，这个已知候选也给出矩阵 SOS 的可行起点。

允许任意 $k>0$ 时，本例

$$
S=\sqrt{1+Z^2},\qquad
\mathbb E[\log S]=\frac1{200}\log101,
$$

所以整体理论范围为

$$
\boxed{B<101^{-1/100}\approx0.95490.}
$$

因此，$0.49$ 是“固定 $k=2$ 且要求指定裕量”的上限，不是所有非整数指数的统一上限。后续扩展 $k$ 的搜索集合时，应相应扩展并重新检查 $B$ 的范围。

### 4.5 完整搜索流程与认证

```text
输入：程序、不变量、初态、目标时间 n、证书模板、随机基、SOS 次数；
      指数集合或区间 K、收缩裕量 ε。

1. 展开 ηθ(F) = qθᵀ b，并认证/计算 Γ(k)。
2. 从收缩条件计算 Bmax；设置 tH = sqrt(Bmax)。
3. 检查上端点可行性，利用二分定位当前编码的最小可行 t 附近。
4. 在可行参数范围内选择多个 t：
   a. 固定 t，解 SDP 合成 ηθ 并减小 ηθ(x0)；
   b. 固定该候选，优化 k，检查 Γ(k)t^k ≤ 1−ε；
   c. 选择需要的有理数 k，重新认证矩上界和完整尾界。
5. 对有希望的 t 区间细化，保留已认证的最佳结果。
```

可将 $t$ 设为 CVXPY 的 `Parameter`；满足 DPP 规则时，重复求解可以复用规范化过程，而不必重新构建整个问题。[^dpp]

最后应检查多项式恒等式、Gram 矩阵半正定性和分布矩上界。固定次数 SOS 失败仅说明当前证明模板未找到证书；无界证明域不能无条件套用依赖 Archimedean 条件的完备性结论，也不能为求解方便加入未认证的状态上界。[^sos]

直接整数矩证书可以作为独立基线保留，其收缩率不能反推为 Cauchy 范数界 $B$。多个有效证书可以按每个 $n$ 取最小尾界；有限参数搜索不自动保证全局最优。若需要整系数 $\eta$，可从已认证的有理系数证书出发，同时缩放 $\eta$ 与边界下界 $a_0$ 清除分母，不能直接对浮点系数取整。

最终的组织方式为

$$
\boxed{
\begin{array}{ll}
\eta\text{ 固定}:&
\text{一个 SDP 求 }B\ \longrightarrow\ \text{优化 }k;\\[1mm]
\eta,k\text{ 都未知}:&
\text{确定 }B\text{ 范围并搜索 }t=\sqrt B
\ \longrightarrow\ \text{固定 }t\text{ 合成 }\eta
\ \longrightarrow\ \text{优化 }k.
\end{array}
}
$$

[^sos]: Hank Yang, *Semidefinite Optimization and Relaxation*, Chapter 4, “Sums of Squares Relaxation”：Gram 矩阵、系数匹配与半代数域上的 SOS 充分证书。<https://hankyang.seas.harvard.edu/Semidefinite/SOS.html>
[^cvx]: CVXPY documentation, *Advanced Constraints*, “Semidefinite matrices”：半正定约束的仿射表达式要求。<https://www.cvxpy.org/tutorial/constraints/index.html>
[^exp]: MOSEK Modeling Cookbook, *Exponential cone optimization*, “Log-sum-exp”：log-sum-exp 的指数锥建模。<https://docs.mosek.com/modeling-cookbook/expo.html>
[^status]: CVXPY documentation, *What is CVXPY?*, “Other problem statuses”：精度不足状态与求解失败的区别。<https://www.cvxpy.org/tutorial/intro/index.html>
[^dpp]: CVXPY documentation, *Disciplined Parametrized Programming*：参数化问题与重复求解。<https://www.cvxpy.org/tutorial/dpp/index.html>

Example：随机仿射控制系统 stochastic affine control system
$x_{t+1} = Ax_t+Bu_t+d+Gw_t$
$x_t$: 状态，$u_t$: 控制输入，$w_t$: 随机扰动，其余参数：系统本身与扰动的作用方式
affine：固定某次扰动后，一次更新为输入和当前状态的仿射表达式

随机仿射动力系统：控制器固定后的闭环模型
采取固定反馈 $u_t = Kx_t$, 代入后得到$x_{t+1} = (A+BK)x_t+Gw_t = A_{cl}x_t + Gw_t$

```
x := 2;
y := 2;

while x*x + y*y > 1 do
    Z :=  0  with probability 99/100
          4  with probability  1/200
         -4  with probability  1/200;

    (x, y) := (
        x/2 + y/4 + Z/8,
        y/2       + Z/8
    )
od
```

