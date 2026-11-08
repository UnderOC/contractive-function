# 三个随机仿射系统：正幂 contractive tail-bound 证书

本目录给出三个带非零加性噪声、无固定步数上限的随机仿射系统。终止条件分别为进入圆、椭圆与三维球。每个例子都附有二次多项式势函数、精确有理收缩常数、覆盖所有分支的不变式，以及可以用 Python 标准库核验的平方和恒等式。

这些是明确可行的证书解；本目录没有声称运行了用户原始的自动合成器。验证程序以有理数检查多项式恒等式和完整区间上的不变式蕴含，不以随机采样替代证明。三个程序的 SHA-256 摘要记在 [certificates.json](certificates.json)，将证书绑定到已检查的顺序赋值程序。

## 1. 统一证书与停止时间

每次循环从当前状态抽取新的分支。令 $\mathbf X_0$ 为给定初始状态，且

$$
T=\inf\{n\ge0:\eta(\mathbf X_n)\le a\}.
$$

程序在 $\eta>a$ 时继续执行，进入 $\eta\le a$ 后停止。每个例子都满足：

$$
\eta\ge0,\qquad
\mathbb E[\eta'\mid\mathbf x]\le\lambda\eta(\mathbf x)+\nu,
\qquad
0<\lambda<1,\quad \nu>0.
$$

选择 $a>0$，使

$$
c=\lambda+\frac{\nu}{a}<1.
$$

因此，对所有守卫状态 $\eta>a$，

$$
\mathbb E[\eta'\mid\mathbf x]\le c\eta(\mathbf x).
$$

采用用户 Markdown 中的正幂模式，取 $k=1$：

$$
V(\mathbf x)=\mathbf 1_{\{\eta(\mathbf x)>a\}}\frac{\eta(\mathbf x)}a.
$$

由于退出后的 $V$ 为零，而 $\eta'\ge0$，即使某个后继状态已经退出，也有

$$
\mathbb E[V(\mathbf X_{n+1})\mid\mathbf X_n=\mathbf x]
\le\frac{\mathbb E[\eta'\mid\mathbf x]}a
\le c V(\mathbf x).
$$

于是对每个整数 $n\ge0$，

$$
\Pr(T>n)\le
\min\left\{1,\frac{\eta_0}{a}\,c^n\right\}.
$$

特别地，下面所有例子均有 $q=c<1$，故这个界还推出 $\Pr(T<\infty)=1$。这里不把“最终停机”作为先验假设。

| 编号 | 结构 | 势函数 $\eta$ | $a$ | $(\lambda,\nu)$ | $c=q$ | $\eta_0/a$ |
|---|---|---|---|---|---|---|
| S1 | 非正规二维耦合，稀有共同冲击 | $x^2+y^2$ | $1/16$ | $(9/16,1/400)$ | $241/400$ | $128$ |
| S2 | 含交叉项的椭球，频繁共同噪声 | $(x-4y)^2+y^2$ | $1/2$ | $(1/4,17/64)$ | $25/32$ | $10$ |
| S3 | 三维随机切换，稀有能量放大分支 | $x^2+y^2+z^2$ | $1/4$ | $(17/64,3/64)$ | $29/64$ | $48$ |

## 2. S1：非正规二维系统与稀有共同冲击

程序文件：[affine_s1_rare_common_shock.pp](affine_s1_rare_common_shock.pp)。

初始状态为 $(x_0,y_0)=(2,2)$。每次迭代抽取

$$
\Pr(\xi=0)=\frac{49}{50},\qquad
\Pr\left(\xi=\frac14\right)=
\Pr\left(\xi=-\frac14\right)=\frac1{100},
$$

执行

$$
\begin{pmatrix}x'\\y'\end{pmatrix}
=
\begin{pmatrix}1/2&3/8\\0&1/2\end{pmatrix}
\begin{pmatrix}x\\y\end{pmatrix}
+\xi\begin{pmatrix}1\\1\end{pmatrix}.
$$

两个坐标使用同一个冲击，而非两个独立噪声。程序中的嵌套概率选择先以 $0.98$ 选择零冲击，再在余下概率 $0.02$ 内等概率选择正负冲击，所以最终概率确为 $49/50,1/100,1/100$。顺序代码先更新 $x$、后更新 $y$，而 $y'$ 不依赖旧 $x$，因而与上述同时更新完全一致。

### 2.1 不变式与退出条件

采用

$$
I_1=\{(x,y):-2\le x\le2,\ -2\le y\le2\}.
$$

对所有噪声值与所有 $I_1$ 内状态，

$$
|x'|\le\frac12\cdot2+\frac38\cdot2+\frac14=2,
\qquad
|y'|\le\frac12\cdot2+\frac14=\frac54<2.
$$

同样的盒不变式在两条赋值之间也成立，因为未赋值的坐标仍在原区间内。这一证明不使用守卫，所以包括所有退出分支。

取

$$
\eta_1=x^2+y^2,\qquad
a_1=\frac1{16},\qquad
\eta_{1,0}=8.
$$

目标为半径 $1/4$ 的闭圆盘；源程序的循环条件为 $x^2+y^2>0.0625$。

### 2.2 精确漂移与平方和证据

噪声均值为零，且 $\mathbb E[\xi^2]=1/800$。因此

$$
\mathbb E[\eta_1']
=
\left(\frac x2+\frac{3y}8\right)^2+\frac{y^2}4+\frac1{400}.
$$

完整的全局恒等式是

$$
\frac9{16}\eta_1+\frac1{400}
-\mathbb E[\eta_1']
=
\frac5{16}\left(x-\frac35y\right)^2+\frac{19}{320}y^2
\ge0.
$$

取 $\lambda_1=9/16,\nu_1=1/400$，得到

$$
c_1=\frac9{16}+\frac{1/400}{1/16}
=\frac{241}{400}.
$$

直接用于守卫域 SOS 检验的证书为

$$
\boxed{
\frac{241}{400}\eta_1-\mathbb E[\eta_1']
=
\frac5{16}\left(x-\frac35y\right)^2
+\frac{19}{320}y^2
+\frac1{25}\left(\eta_1-\frac1{16}\right).
}
$$

右侧是两个非负平方项与一个正的常数乘子乘以闭守卫多项式。它在 $\eta_1\ge1/16$ 上非负，因而也覆盖程序的严格守卫 $\eta_1>1/16$。

### 2.3 Tail bound

$$
\boxed{
\Pr(T_1>n)\le
\min\left\{1,128\left(\frac{241}{400}\right)^n\right\}.
}
$$

该证书从 $n=19$ 起给出 $\Pr(T_1>n)\le0.01$。这是所列公式的保证，不是实际分布的精确分位数。

## 3. S2：含交叉项的椭球证书

程序文件：[affine_s2_cross_term.pp](affine_s2_cross_term.pp)。

初始状态为 $(x_0,y_0)=(2,1)$。每次独立抽取 $\xi\in\{-1,+1\}$，两值各以概率 $1/2$ 出现，并执行

$$
x'=\frac12x-y+\xi,\qquad
y'=\frac14y+\frac18\xi.
$$

令

$$
u=x-4y,\qquad v=y.
$$

则完整随机变换成为

$$
u'=\frac12u+\frac12\xi,\qquad
v'=\frac14v+\frac18\xi.
$$

取二次势函数

$$
\eta_2=u^2+v^2=(x-4y)^2+y^2
=
\begin{pmatrix}x&y\end{pmatrix}
\begin{pmatrix}1&-4\\-4&17\end{pmatrix}
\begin{pmatrix}x\\y\end{pmatrix}.
$$

其矩阵的首个主子式为 $1$、行列式为 $1$，所以正定。这个选择显式包含交叉项 $-8xy$。原坐标中的确定性矩阵

$$
A=\begin{pmatrix}1/2&-1\\0&1/4\end{pmatrix}
$$

会把方向 $(0,y)$ 的欧氏平方范数从 $y^2$ 放大到 $17y^2/16$；这个事实说明为什么在本例中使用不同于欧氏范数的二次型是有意义的，并不表示系统具有大于一的特征值。

### 3.1 不变式与顺序赋值的中间断言

采用

$$
I_2=\{(x,y):|x-4y|\le2,\ |y|\le1\}.
$$

在 $(u,v)$ 坐标中，

$$
|u'|\le1+\frac12=\frac32<2,\qquad
|v'|\le\frac14+\frac18=\frac38<1,
$$

所以 $I_2$ 覆盖初始状态和全部后继，包括退出状态。

源程序先更新 $x$，再更新 $y$，保持同时更新语义。两条赋值之间不直接重复循环不变式，而使用以下分支断言。记 $x_{\rm mid}$ 为已经更新的 $x$，$y$ 仍为旧值：

$$
x_{\rm mid}-y=\frac12u+\xi.
$$

因此，正冲击分支满足

$$
0\le x_{\rm mid}-y\le2,\qquad -1\le y\le1,
$$

负冲击分支满足

$$
-2\le x_{\rm mid}-y\le0,\qquad -1\le y\le1.
$$

对满足各自中间断言的任意状态，令 $q=x_{\rm mid}-y$，执行第二条赋值后，

$$
u'=q-\frac12\xi,\qquad
y'=\frac14y+\frac18\xi.
$$

正分支给出 $u'\in[-1/2,3/2]$，负分支给出 $u'\in[-3/2,1/2]$，且均有 $|y'|\le3/8$。所以这是真正针对完整中间断言域的局部证明，不仅对某些可达状态成立。

### 3.2 精确漂移与守卫证书

取

$$
a_2=\frac12,\qquad
\eta_{2,0}=(-2)^2+1^2=5.
$$

目标为椭圆 $\eta_2\le1/2$。对所有状态，

$$
\mathbb E[\eta_2']
=
\frac14u^2+\frac1{16}v^2+\frac{17}{64}
=
\frac14\eta_2+\frac{17}{64}-\frac3{16}y^2.
$$

因此可取

$$
\lambda_2=\frac14,\qquad \nu_2=\frac{17}{64},\qquad
c_2=\frac14+\frac{17/64}{1/2}=\frac{25}{32}.
$$

完整的守卫域恒等式为

$$
\boxed{
\frac{25}{32}\eta_2-\mathbb E[\eta_2']
=
\frac3{16}y^2+
\frac{17}{32}\left(\eta_2-\frac12\right).
}
$$

### 3.3 Tail bound

$$
\boxed{
\Pr(T_2>n)\le
\min\left\{1,10\left(\frac{25}{32}\right)^n\right\}.
}
$$

该证书从 $n=28$ 起给出 $\Pr(T_2>n)\le0.01$。本例噪声每一步都非零；不能把确定性轨迹收敛性当作随机停止时间的证明。

## 4. S3：三维随机切换，允许稀有分支瞬时放大能量

程序文件：[affine_s3_switched_3d.pp](affine_s3_switched_3d.pp)。

初始状态为 $(x_0,y_0,z_0)=(2,2,2)$。每次先选择模式，再独立选择噪声符号：

$$
\Pr(M=0)=\frac78,\qquad \Pr(M=1)=\frac18,\qquad
\Pr(\xi=1/8)=\Pr(\xi=-1/8)=\frac12.
$$

系统为

$$
\begin{pmatrix}x'\\y'\\z'\end{pmatrix}
=
A_M\begin{pmatrix}x\\y\\z\end{pmatrix}
+\xi\begin{pmatrix}1\\-1\\1\end{pmatrix},
$$

其中

$$
A_0=\frac14 I_3,\qquad
A_1=
\begin{pmatrix}
3/4&0&0\\
3/4&0&0\\
3/4&0&0
\end{pmatrix}.
$$

四个完整分支的概率依次为 $7/16,7/16,1/16,1/16$。程序中先更新 $y$，再更新 $z$，最后更新 $x$。因此稀有模式中的三条赋值都使用旧 $x$，没有顺序赋值造成的额外收缩。

稀有模式对于方向 $(x,0,0)$ 具有

$$
\frac{\|A_1(x,0,0)^\top\|_2^2}{x^2}=\frac{27}{16}>1.
$$

这是某些方向上的瞬时能量放大。$A_1$ 的谱半径仍为 $3/4$，所以不把它称为具有不稳定特征值的模式。下面的证明允许这一分支，并使用完整混合分布的期望。

### 4.1 不变式与目标

采用

$$
I_3=[-2,2]^3,\qquad
\eta_3=x^2+y^2+z^2,\qquad
a_3=\frac14.
$$

常见模式的任一新坐标绝对值最多为

$$
\frac14\cdot2+\frac18=\frac58,
$$

稀有模式的任一新坐标绝对值最多为

$$
\frac34\cdot2+\frac18=\frac{13}{8}<2.
$$

所以每个赋值位置都保持同一个盒不变式。目标为半径 $1/2$ 的闭球，且 $\eta_{3,0}=12$。

### 4.2 精确漂移与守卫证书

噪声总平方贡献为 $3/64$。两个模式混合后，

$$
\begin{aligned}
\mathbb E[\eta_3']
&=\frac78\frac{\eta_3}{16}
+\frac18\frac{27x^2}{16}
+\frac3{64}\\
&=\frac{17}{64}x^2
+\frac7{128}(y^2+z^2)
+\frac3{64}\\
&=\frac{17}{64}\eta_3+\frac3{64}
-\frac{27}{128}(y^2+z^2).
\end{aligned}
$$

因此

$$
\lambda_3=\frac{17}{64},\qquad
\nu_3=\frac3{64},\qquad
c_3=\frac{17}{64}+\frac{3/64}{1/4}=\frac{29}{64}.
$$

精确证书为

$$
\boxed{
\frac{29}{64}\eta_3-\mathbb E[\eta_3']
=
\frac{27}{128}(y^2+z^2)
+\frac3{16}\left(\eta_3-\frac14\right).
}
$$

### 4.3 Tail bound

$$
\boxed{
\Pr(T_3>n)\le
\min\left\{1,48\left(\frac{29}{64}\right)^n\right\}.
}
$$

该证书从 $n=11$ 起给出 $\Pr(T_3>n)\le0.01$。

## 5. 接入证书求解与复核

三个 $\eta$ 的次数都是二，所有分支更新都是仿射，因此 $\mathbb E[\eta']$ 仍然是二次多项式。可直接给求解器二次型模板

$$
\eta(\mathbf x)=\mathbf x^\top P\mathbf x
$$

并将上文给出的 $P,a,c$ 作为可行参考解。每个证书都具有低次数结构

$$
c\eta-\mathbb E[\eta']
=\sigma_0+\sigma_1(\eta-a),
$$

其中 $\sigma_0$ 是显式非负有理加权平方和，$\sigma_1$ 是正常数。这里不需要加入高次数不变式乘子来证明漂移；不变式单独用精确仿射区间界验证。

全部源程序常数为有限小数。程序末尾的 “refute true” 沿用原例子的规范形式，统计所有有限退出。它不施加固定执行期限。

执行精确校验：

~~~bash
python verify_positive.py
~~~

预期输出：

~~~text
S1: PASS; c=241/400; prefactor=128; certified Pr(T>n)<=0.01 for n>=19
S2: PASS; c=25/32; prefactor=10; certified Pr(T>n)<=0.01 for n>=28
S3: PASS; c=29/64; prefactor=48; certified Pr(T>n)<=0.01 for n>=11
Verified 26 exact polynomial identities and 28 full-domain affine interval implications; no sampling or optimizer.
~~~

该脚本核验二次势函数、完整分支概率、条件一阶矩、全局与守卫域漂移恒等式、正乘子、初始值、尾界常数及不变式。S2 还单独检验两个中间断言域上到最终不变式的蕴含。源码解释器对有限深度执行树的检查可用于发现顺序赋值或语法错误；它只是补充检查，通用证明来自上述全域恒等式和区间蕴含。
