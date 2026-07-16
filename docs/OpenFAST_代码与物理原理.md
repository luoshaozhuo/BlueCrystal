# OpenFAST 代码与物理原理：从主程序、模块数据结构到约束 DAE 与 Tight Coupling

> 目标：从 OpenFAST 的入口程序和 glue code 出发，逐步建立对模块数据结构、结构动力学、
> 约束状态、时间积分、模块耦合、残差与 Newton 迭代的统一理解。本文重点服务于后续
> 继续阅读 `FAST_InitializeAll_T`、`FAST_Solution0_T`、`FAST_Solution_T`、
> `FAST_Linearize_T`、`FAST_Solver.f90`、`FAST_ModGlue.f90` 等源码。

---

## 1. OpenFAST 的整体定位

OpenFAST 不是一个单一物理方程的求解器，而是一个多模块、多物理场耦合框架。
典型模块包括 ElastoDyn、BeamDyn、AeroDyn、InflowWind、ServoDyn、HydroDyn、
SeaState、SubDyn 和 MoorDyn 等。

OpenFAST 的 glue code 负责：

1. 初始化各模块；
2. 管理各模块的状态、输入、输出和参数；
3. 建立模块之间的变量和 Mesh 映射；
4. 组织全局时间推进；
5. 在 tight coupling 模式下构造耦合残差并迭代求解；
6. 组织线性化、输出和 checkpoint。

因此，应把 OpenFAST 看成：

$$
\boxed{
\text{物理模块集合}
+
\text{模块间映射}
+
\text{全局耦合与时间推进}
}
$$

---

## 2. `FAST_Prog.f90`：OpenFAST 命令行程序入口

`FAST_Prog.f90` 是 Fortran 主程序。它的职责不是直接计算气动力、结构响应或水动力，而是组织整个仿真生命周期。

```text
启动程序
  ↓
初始化 NWTC Library
  ↓
解析命令行参数
  ↓
普通初始化 / Restart / VTKLin / SteadyState
  ↓
FAST_InitializeAll_T
  ↓
FAST_Solution0_T
  ↓
时间步循环
    ├─ FAST_Solution_T
    ├─ FAST_Linearize_T
    └─ checkpoint / output
  ↓
退出与清理
```

四个核心顶层函数是：

- `FAST_InitializeAll_T`
- `FAST_Solution0_T`
- `FAST_Solution_T`
- `FAST_Linearize_T`

---

## 3. `FAST_InitializeAll_T` 的职责

`FAST_InitializeAll_T` 是整机仿真的总初始化入口。它本身不是一个动力学求解器，而是一个装配过程。

它的主要工作包括：

1. 读取 `.fst` 主输入文件；
2. 设置全局时间参数；
3. 根据模块开关初始化各物理模块；
4. 分配模块状态、输入历史、输出和工作区；
5. 注册模块变量；
6. 建立模块间映射；
7. 初始化 tight-coupling solver；
8. 初始化线性化相关数据；
9. 最终形成完整的 `FAST_TurbineType`。

$$
\boxed{
\text{输入文件}
+
\text{外部初始化数据}
\longrightarrow
\text{完整的 } FAST\_TurbineType
}
$$

---

## 4. `FAST_TurbineType` 与模块统一数据结构

```text
FAST_TurbineType
  ├─ p_FAST
  ├─ y_FAST
  ├─ m_FAST
  ├─ p_Glue
  ├─ y_Glue
  ├─ m_Glue
  ├─ ED
  ├─ BD
  ├─ AD
  ├─ SrvD
  ├─ IfW
  ├─ SeaSt
  ├─ HD
  ├─ SD
  ├─ Mooring modules
  └─ 其他模块
```

统一数据分类：

- `p`：参数；
- `x`：连续状态；
- `xd`：离散状态；
- `z`：约束状态；
- `OtherSt`：其他状态；
- `u` 或 `Input`：模块输入；
- `y`：模块输出；
- `m`：模块内部工作变量。

模块可抽象成：

$$
\dot{\boldsymbol{x}}
=
\boldsymbol{f}
\left(
\boldsymbol{x},
\boldsymbol{x}_d,
\boldsymbol{z},
\boldsymbol{u},
t;
\boldsymbol{p}
\right)
$$

$$
\boldsymbol{x}_{d,n+1}
=
\boldsymbol{f}_d
\left(
\boldsymbol{x}_n,
\boldsymbol{x}_{d,n},
\boldsymbol{z}_n,
\boldsymbol{u}_n,
t_n;
\boldsymbol{p}
\right)
$$

$$
\boldsymbol{0}
=
\boldsymbol{c}
\left(
\boldsymbol{x},
\dot{\boldsymbol{x}},
\boldsymbol{x}_d,
\boldsymbol{z},
\boldsymbol{u},
t;
\boldsymbol{p}
\right)
$$

$$
\boldsymbol{y}
=
\boldsymbol{g}
\left(
\boldsymbol{x},
\boldsymbol{x}_d,
\boldsymbol{z},
\boldsymbol{u},
t;
\boldsymbol{p}
\right)
$$

---

## 5. `CalcContStateDeriv` 的含义

`Cont` 是 `Continuous` 的缩写，不是 `Constant`。

```text
CalcContStateDeriv
= Calculate Continuous-State Derivatives
= 计算连续状态导数
```

若结构模块的连续状态写成：

$$
\boldsymbol{x}
=
\begin{bmatrix}
\boldsymbol{q}\\
\boldsymbol{v}
\end{bmatrix},
\qquad
\boldsymbol{v}
=
\dot{\boldsymbol{q}}
$$

则：

$$
\dot{\boldsymbol{x}}
=
\begin{bmatrix}
\boldsymbol{v}\\
\boldsymbol{a}
\end{bmatrix}
$$

因此，结构模块的 `CalcContStateDeriv` 往往会返回包含速度和加速度在内的连续状态导数。

---

## 6. ElastoDyn 与 BeamDyn

ElastoDyn 和 BeamDyn 是并列模块，不是包含关系。

### 6.1 ElastoDyn

ElastoDyn 是低阶整机结构动力学模块，通常负责平台、塔架低阶模态、机舱与偏航、传动链、轮毂及可选的简化叶片模态。

### 6.2 BeamDyn

BeamDyn 是高保真叶片梁动力学模块，主要负责叶片大变形、弯扭耦合和几何精确梁动力学。

### 6.3 两者耦合

- ElastoDyn 提供轮毂和叶根运动；
- BeamDyn 计算叶片柔性响应；
- AeroDyn 向 BeamDyn 或结构模块提供气动力；
- 叶片载荷反馈到整机结构系统。

$$
\boxed{
\text{ElastoDyn：整机结构骨架}
\qquad
\text{BeamDyn：叶片高保真梁}
}
$$

---

## 7. OpenFAST 中的 Mesh

OpenFAST 的 `Mesh` 不是狭义的有限元网格，而是模块间交换空间分布物理量的接口数据结构。

Motion Mesh 传递：

- 位置；
- 姿态；
- 线速度；
- 角速度；
- 线加速度；
- 角加速度。

Load Mesh 传递：

- 力；
- 力矩；
- 分布载荷；
- 集中载荷。

关键区别：

$$
\boxed{
\text{模块内部自由度}
\neq
\text{模块间交换点}
}
$$

---

## 8. 模块间映射

基本关系：

$$
\boxed{
\boldsymbol{u}_j
=
\mathcal{T}_{i\rightarrow j}
\left(
\boldsymbol{y}_i
\right)
}
$$

映射包括：

- 普通变量复制；
- 坐标系转换；
- 空间插值；
- 运动学传递；
- 载荷传递；
- 力矩平移；
- 分布载荷等效；
- 自定义映射。

例如：

$$
\boldsymbol{v}_B
=
\boldsymbol{v}_A
+
\boldsymbol{\omega}_A
\times
\boldsymbol{r}_{AB}
$$

$$
\boldsymbol{M}_A
=
\boldsymbol{M}_B
+
\boldsymbol{r}_{AB}
\times
\boldsymbol{F}_B
$$

---

## 9. `m_Glue%ModData` 与组合变量视图

`m_Glue%ModData` 不是各模块真实状态的集中副本。真实数据仍然存放在：

```text
Turbine%ED
Turbine%BD
Turbine%AD
Turbine%SrvD
...
```

`m_Glue%ModData` 更接近模块登记表、模块 ID、实例号、时间步信息、变量目录和 glue 层索引。

`ModGlueType%Vars` 承担组合模块变量视图的作用，为 mapping、Jacobian、线性化和变量查找提供统一索引空间。

---

## 10. 半离散结构动力学方程

“半离散”指空间已离散、时间仍连续。

连续体动量平衡：

$$
\rho\ddot{\boldsymbol{u}}
=
\nabla\cdot\boldsymbol{\sigma}
+
\rho\boldsymbol{b}
$$

空间离散：

$$
\boldsymbol{u}(\boldsymbol{x},t)
\approx
\boldsymbol{N}(\boldsymbol{x})
\boldsymbol{q}(t)
$$

得到：

$$
\boxed{
\boldsymbol{M}\ddot{\boldsymbol{q}}
+
\boldsymbol{f}_{\mathrm{int}}(\boldsymbol{q})
=
\boldsymbol{f}_{\mathrm{ext}}
}
$$

线性情况下：

$$
\boxed{
\boldsymbol{M}\ddot{\boldsymbol{q}}
+
\boldsymbol{C}\dot{\boldsymbol{q}}
+
\boldsymbol{K}\boldsymbol{q}
=
\boldsymbol{f}(t)
}
$$

---

## 11. 质量、科氏和离心项

设：

$$
T
=
\frac12
\sum_{j,k}
M_{jk}(\boldsymbol{q})
\dot q_j\dot q_k
$$

则：

$$
\frac{\partial T}{\partial\dot q_i}
=
\sum_jM_{ij}\dot q_j
$$

$$
\frac{d}{dt}
\left(
\frac{\partial T}{\partial\dot q_i}
\right)
=
\sum_jM_{ij}\ddot q_j
+
\sum_{j,k}
\frac{\partial M_{ij}}{\partial q_k}
\dot q_j\dot q_k
$$

$$
\frac{\partial T}{\partial q_i}
=
\frac12
\sum_{j,k}
\frac{\partial M_{jk}}{\partial q_i}
\dot q_j\dot q_k
$$

最终：

$$
\frac{d}{dt}
\left(
\frac{\partial T}{\partial\dot q_i}
\right)
-
\frac{\partial T}{\partial q_i}
=
\sum_jM_{ij}\ddot q_j
+
\sum_{j,k}
\Gamma_{ijk}\dot q_j\dot q_k
$$

其中：

$$
\Gamma_{ijk}
=
\frac12
\left(
\frac{\partial M_{ij}}{\partial q_k}
+
\frac{\partial M_{ik}}{\partial q_j}
-
\frac{\partial M_{jk}}{\partial q_i}
\right)
$$

原来的一个速度二次项，是利用 $j,k$ 对称性平均拆分后形成 Christoffel 符号中的三个质量矩阵导数，并非凭空增加。

---

## 12. 重力、弹性势力和阻尼

重力势能：

$$
V_g(\boldsymbol{q})
=
\sum_a m_agz_a(\boldsymbol{q})
$$

$$
G_i(\boldsymbol{q})
=
\frac{\partial V_g}{\partial q_i}
$$

弹性势能：

$$
f_{e,i}
=
\frac{\partial V_e}{\partial q_i}
$$

粘性阻尼：

$$
Q_i^d
=
-\sum_jD_{ij}\dot q_j
$$

统一分析力学形式：

$$
\boxed{
\sum_jM_{ij}\ddot q_j
+
\sum_{j,k}\Gamma_{ijk}\dot q_j\dot q_k
+
\sum_jD_{ij}\dot q_j
+
\frac{\partial V_g}{\partial q_i}
+
\frac{\partial V_e}{\partial q_i}
=
Q_i^{\mathrm{ext}}
+
Q_i^c
}
$$

---

## 13. 从 Newton 动力学到 d’Alembert 原理

对第 $a$ 个质点：

$$
m_a\ddot{\boldsymbol{r}}_a
=
\boldsymbol{F}_a^{\mathrm{appl}}
+
\boldsymbol{R}_a
$$

对于理想约束，约束反力对允许虚位移不做虚功：

$$
\sum_a
\boldsymbol{R}_a
\cdot
\delta\boldsymbol{r}_a
=
0
$$

于是：

$$
\boxed{
\sum_a
\left(
\boldsymbol{F}_a^{\mathrm{appl}}
-
m_a\ddot{\boldsymbol{r}}_a
\right)
\cdot
\delta\boldsymbol{r}_a
=
0
}
$$

这就是 d’Alembert 原理。

---

## 14. 为什么虚位移必须满足约束

虚位移是固定时刻下，从当前可行构型到相邻可行构型的无穷小变化。

若：

$$
\phi_\alpha(\boldsymbol{q},t)=0
$$

则：

$$
\delta\phi_\alpha
=
\sum_i
\frac{\partial\phi_\alpha}{\partial q_i}
\delta q_i
=
0
$$

即：

$$
\boldsymbol{G}\delta\boldsymbol{q}=0
$$

允许虚位移位于约束流形的切空间。

---

## 15. 为什么理想约束反力不做虚功

理想约束定义：

$$
\delta W_c
=
\boldsymbol{Q}_c^T
\delta\boldsymbol{q}
=
0
$$

由于：

$$
\delta\boldsymbol{q}
\in
\ker(\boldsymbol{G})
$$

约束广义力属于：

$$
\operatorname{Range}(\boldsymbol{G}^T)
$$

所以存在：

$$
\boldsymbol{Q}_c
=
\boldsymbol{G}^T\boldsymbol{\lambda}
$$

于是：

$$
\delta W_c
=
\boldsymbol{\lambda}^T
\boldsymbol{G}\delta\boldsymbol{q}
=
0
$$

这不是所有约束自动成立的性质，而是理想约束的物理假设。

---

## 16. 独立坐标与冗余坐标

独立最小坐标：约束已被坐标参数化自动满足，$\delta q_i$ 相互独立，得到普通 Lagrange 方程。

冗余坐标：保留：

$$
\phi_\alpha(\boldsymbol{q},t)=0
$$

此时：

$$
\boldsymbol{G}\delta\boldsymbol{q}=0
$$

需要引入拉格朗日乘子：

$$
\frac{d}{dt}
\left(
\frac{\partial L}{\partial\dot q_i}
\right)
-
\frac{\partial L}{\partial q_i}
=
Q_i^{\mathrm{nc}}
+
\sum_\alpha
\lambda_\alpha
\frac{\partial\phi_\alpha}{\partial q_i}
$$

并保留：

$$
\phi_\alpha(\boldsymbol{q},t)=0
$$

因此形成 DAE。

---

## 17. 约束状态的物理图像：冗余坐标单摆

取：

$$
\boldsymbol{q}
=
\begin{bmatrix}
x\\
y
\end{bmatrix}
$$

约束：

$$
x^2+y^2-L^2=0
$$

动力学：

$$
m\ddot x+\lambda x=0
$$

$$
m\ddot y+\lambda y+mg=0
$$

连续状态：

$$
x,\ y,\ \dot x,\ \dot y
$$

约束状态：

$$
z=\lambda
$$

$\lambda$ 不是通过独立微分方程积分得到，而是由当前动力学与约束条件联立求出。

---

## 18. 约束 DAE

一般约束系统：

$$
\boldsymbol{M}(\boldsymbol{q})\ddot{\boldsymbol{q}}
+
\boldsymbol{h}(\boldsymbol{q},\dot{\boldsymbol{q}},t)
=
\boldsymbol{Q}_{\mathrm{ext}}
+
\boldsymbol{G}^T\boldsymbol{\lambda}
$$

$$
\boldsymbol{\phi}(\boldsymbol{q},t)=0
$$

约束微分到加速度级：

$$
\boldsymbol{G}\ddot{\boldsymbol{q}}
=
\boldsymbol{\gamma}
(\boldsymbol{q},\dot{\boldsymbol{q}},t)
$$

增广系统：

$$
\boxed{
\begin{bmatrix}
\boldsymbol{M} & -\boldsymbol{G}^T\\
\boldsymbol{G} & \boldsymbol{0}
\end{bmatrix}
\begin{bmatrix}
\ddot{\boldsymbol{q}}\\
\boldsymbol{\lambda}
\end{bmatrix}
=
\begin{bmatrix}
\boldsymbol{Q}_{\mathrm{ext}}-\boldsymbol{h}\\
\boldsymbol{\gamma}
\end{bmatrix}
}
$$

---

## 19. 为什么拉格朗日乘子不能替代约束方程

拉格朗日乘子法只是把约束反力表示成：

$$
\boldsymbol{Q}_c
=
\boldsymbol{G}^T\boldsymbol{\lambda}
$$

未知量增加了 $m$ 个乘子，所以仍需保留 $m$ 个约束方程：

$$
\phi_1=0,\ldots,\phi_m=0
$$

最终：

- $n$ 个动力学方程；
- $m$ 个约束方程；

共同求解：

- $n$ 个加速度；
- $m$ 个拉格朗日乘子。

---

## 20. 从动力学方程到 Lagrange 方程

设：

$$
\boldsymbol{r}_a
=
\boldsymbol{r}_a(q_1,\ldots,q_n,t)
$$

$$
\delta\boldsymbol{r}_a
=
\sum_i
\frac{\partial\boldsymbol{r}_a}{\partial q_i}
\delta q_i
$$

广义力：

$$
Q_i
=
\sum_a
\boldsymbol{F}_a
\cdot
\frac{\partial\boldsymbol{r}_a}{\partial q_i}
$$

利用：

$$
\sum_a
m_a\ddot{\boldsymbol{r}}_a
\cdot
\frac{\partial\boldsymbol{r}_a}{\partial q_i}
=
\frac{d}{dt}
\left(
\frac{\partial T}{\partial\dot q_i}
\right)
-
\frac{\partial T}{\partial q_i}
$$

得到：

$$
\boxed{
\frac{d}{dt}
\left(
\frac{\partial T}{\partial\dot q_i}
\right)
-
\frac{\partial T}{\partial q_i}
=
Q_i
}
$$

若定义：

$$
L=T-V
$$

则：

$$
\boxed{
\frac{d}{dt}
\left(
\frac{\partial L}{\partial\dot q_i}
\right)
-
\frac{\partial L}{\partial q_i}
=
Q_i^{\mathrm{nc}}
}
$$

---

## 21. 从动力学方程到 Hamilton 原理

从 Lagrange 方程出发，乘 $\delta q_i$ 并对时间积分；对含时间导数的一项分部积分，并使用固定端点条件：

$$
\delta q_i(t_1)=\delta q_i(t_2)=0
$$

得到：

$$
\boxed{
\delta
\int_{t_1}^{t_2}
L(q,\dot q,t)\,dt
=
0
}
$$

逻辑链条：

$$
\boxed{
\text{Newton 方程}
\rightarrow
\text{d’Alembert 原理}
\rightarrow
\text{Lagrange 方程}
\rightarrow
\text{Hamilton 原理}
}
$$

---

## 22. Newmark 方法

$$
\boldsymbol{q}_{n+1}
=
\boldsymbol{q}_n
+
h\dot{\boldsymbol{q}}_n
+
h^2
\left[
\left(
\frac12-\beta
\right)
\ddot{\boldsymbol{q}}_n
+
\beta
\ddot{\boldsymbol{q}}_{n+1}
\right]
$$

$$
\dot{\boldsymbol{q}}_{n+1}
=
\dot{\boldsymbol{q}}_n
+
h
\left[
(1-\gamma)
\ddot{\boldsymbol{q}}_n
+
\gamma
\ddot{\boldsymbol{q}}_{n+1}
\right]
$$

当前时间步的微分问题可转成关于当前加速度的代数方程。

---

## 23. generalized-α 方法

$$
\boldsymbol{a}_{n+\alpha_m}
=
(1-\alpha_m)\boldsymbol{a}_{n+1}
+
\alpha_m\boldsymbol{a}_n
$$

$$
\boldsymbol{q}_{n+\alpha_f}
=
(1-\alpha_f)\boldsymbol{q}_{n+1}
+
\alpha_f\boldsymbol{q}_n
$$

$$
\boldsymbol{v}_{n+\alpha_f}
=
(1-\alpha_f)\boldsymbol{v}_{n+1}
+
\alpha_f\boldsymbol{v}_n
$$

动力学平衡：

$$
\boldsymbol{M}
\boldsymbol{a}_{n+\alpha_m}
+
\boldsymbol{C}
\boldsymbol{v}_{n+\alpha_f}
+
\boldsymbol{f}_{\mathrm{int}}
\left(
\boldsymbol{q}_{n+\alpha_f}
\right)
=
\boldsymbol{f}_{\mathrm{ext}}
\left(
t_{n+\alpha_f}
\right)
$$

它是隐式时间积分方法，不是 Newton 法。

---

## 24. Newton 法与残差

求解：

$$
\boldsymbol{F}(\boldsymbol{x})=\boldsymbol{0}
$$

Taylor 展开：

$$
\boldsymbol{F}
\left(
\boldsymbol{x}^{(k)}
+
\Delta\boldsymbol{x}^{(k)}
\right)
\approx
\boldsymbol{F}
\left(
\boldsymbol{x}^{(k)}
\right)
+
\boldsymbol{J}^{(k)}
\Delta\boldsymbol{x}^{(k)}
$$

令下一步近似满足方程，得到：

$$
\boxed{
\boldsymbol{J}^{(k)}
\Delta\boldsymbol{x}^{(k)}
=
-
\boldsymbol{F}
\left(
\boldsymbol{x}^{(k)}
\right)
}
$$

若定义：

$$
\boldsymbol{R}
=
-\boldsymbol{F}
$$

则：

$$
\boxed{
\boldsymbol{J}
\Delta\boldsymbol{x}
=
\boldsymbol{R}
}
$$

---

## 25. Newton 法与梯度下降

Newton 求根：

$$
\boldsymbol{F}(\boldsymbol{x})=0
$$

$$
\boldsymbol{J}_F
\Delta\boldsymbol{x}
=
-\boldsymbol{F}
$$

梯度下降：

$$
\min_{\boldsymbol{x}}
\Phi(\boldsymbol{x})
$$

$$
\boldsymbol{x}^{(k+1)}
=
\boldsymbol{x}^{(k)}
-
\eta
\nabla\Phi
$$

Newton 优化：

$$
\boldsymbol{H}
\Delta\boldsymbol{x}
=
-
\nabla\Phi
$$

所以：

- 梯度下降只用梯度；
- Newton 求根使用 Jacobian；
- Newton 优化使用 Hessian。

---

## 26. DAE 的 Newmark/Newton 求解

未知量可选为：

$$
\boldsymbol{w}_{n+1}
=
\begin{bmatrix}
\ddot{\boldsymbol{q}}_{n+1}\\
\boldsymbol{\lambda}_{n+1}
\end{bmatrix}
$$

残差：

$$
\boldsymbol{R}
=
\begin{bmatrix}
\boldsymbol{M}\ddot{\boldsymbol{q}}
+
\boldsymbol{h}
-
\boldsymbol{G}^T\boldsymbol{\lambda}
-
\boldsymbol{Q}_{\mathrm{ext}}
\\
\boldsymbol{\phi}(\boldsymbol{q},t)
\end{bmatrix}
$$

Newton 迭代：

$$
\boldsymbol{J}^{(k)}
\Delta\boldsymbol{w}^{(k)}
=
-
\boldsymbol{R}^{(k)}
$$

$$
\boldsymbol{w}^{(k+1)}
=
\boldsymbol{w}^{(k)}
+
\Delta\boldsymbol{w}^{(k)}
$$

---

## 27. Loose Coupling 与 Tight Coupling

Loose coupling：模块按顺序推进，通常使用上一时刻或外推输入，当前时间步内不迭代到完全一致。

Tight coupling：在每个时间步内反复迭代，直到状态导数、模块输入以及必要的约束状态一致。

---

## 28. OpenFAST Tight Coupling 的宏观流程

已知：

$$
\boldsymbol{q}_n,
\quad
\boldsymbol{v}_n,
\quad
\boldsymbol{a}_n,
\quad
\boldsymbol{u}_n
$$

每个时间步内反复执行：

1. 猜测：
   $$
   \boldsymbol{a}_{n+1}^{(k)},
   \quad
   \boldsymbol{u}_{n+1}^{(k)}
   $$
2. 用 generalized-α 计算：
   $$
   \boldsymbol{q}_{n+1}^{(k)},
   \quad
   \boldsymbol{v}_{n+1}^{(k)}
   $$
3. 各模块计算：
   $$
   \widehat{\boldsymbol{a}}^{(k)},
   \quad
   \boldsymbol{y}^{(k)}
   $$
4. 模块间映射：
   $$
   \widehat{\boldsymbol{u}}^{(k)}
   =
   \mathcal{T}
   \left(
   \boldsymbol{y}^{(k)}
   \right)
   $$
5. 形成残差：
   $$
   \boldsymbol{R}_a^{(k)}
   =
   \widehat{\boldsymbol{a}}^{(k)}
   -
   \boldsymbol{a}^{(k)}
   $$
   $$
   \boldsymbol{R}_u^{(k)}
   =
   \widehat{\boldsymbol{u}}^{(k)}
   -
   \boldsymbol{u}^{(k)}
   $$
6. 用 Jacobian 求修正：
   $$
   \boldsymbol{J}^{(k)}
   \Delta\boldsymbol{w}^{(k)}
   =
   -
   \boldsymbol{R}^{(k)}
   $$
7. 更新并继续迭代；
8. 收敛后提交当前时间步状态。

---

## 29. Fixed Jacobian 与 Adaptive Jacobian

Fixed Jacobian Updates：按固定时间间隔或步数更新 Jacobian，中间迭代复用旧 Jacobian，属于 modified Newton。

Adaptive Jacobian Updates：默认复用 Jacobian，但当残差下降停滞或收敛失败时自动重算，以兼顾效率和鲁棒性。

---

## 30. 后续源码阅读框架

后续应始终区分：

1. 模块内部动力学；
2. glue mapping；
3. 时间离散；
4. 非线性耦合求解；
5. 模块内部约束状态；
6. 机械约束的拉格朗日乘子；
7. 模块输入输出一致性残差。

不能把所有 `z` 都等同于机械约束反力，也不能把所有 OpenFAST 模块都默认成同一种 DAE。

---

## 31. 建议的后续学习顺序

1. `FAST_InitializeAll_T`
2. `FAST_Solution0_T`
3. `FAST_Solution_T`
4. `FAST_SolverStep`
5. `FAST_ModGlue`
6. `FAST_Mapping`
7. `FAST_Linearize_T`
8. `ElastoDyn.f90`
9. `ElastoDyn_Types.f90`
10. `ElastoDyn_Registry.txt`
11. BeamDyn 状态与求解算法
12. OpenFAST Jacobian 四个分块的具体含义

---

## 32. 核心结论

OpenFAST 主线：

$$
\boxed{
\text{单模块方程}
+
\text{模块间映射}
+
\text{时间积分}
+
\text{耦合残差}
+
\text{Newton 修正}
}
$$

分析力学主线：

$$
\boxed{
\text{Newton 动力学}
\rightarrow
\text{d’Alembert 原理}
\rightarrow
\text{Lagrange 方程}
\rightarrow
\text{Hamilton 原理}
}
$$

约束系统主线：

$$
\boxed{
\text{冗余坐标}
\rightarrow
\text{约束方程}
\rightarrow
\text{拉格朗日乘子}
\rightarrow
\text{DAE}
}
$$

数值求解主线：

$$
\boxed{
\text{时间离散}
\rightarrow
\text{非线性代数方程}
\rightarrow
\text{残差}
\rightarrow
\text{Jacobian}
\rightarrow
\text{Newton 迭代}
}
$$

这三条主线最终在 OpenFAST 的 tight-coupling solver 中汇合。
