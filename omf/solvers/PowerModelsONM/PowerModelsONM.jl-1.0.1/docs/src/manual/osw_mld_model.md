# [Optimal Switching / Load shed Mathematical Model](@id osw-mld-math)

The following contains the mathematical model for the optimal switching / load shed problem as implemented in PowerModelsONM.

For more information about notation see the [optimal dispatch documentation](@ref opf-math), or [PowerModelsDistribution AC OPF documentation](https://lanl-ansi.github.io/PowerModelsDistribution.jl/stable/manual/math-model.html).

## OSW/MLD Variables

```math
\begin{align}
\mbox{variables: } & \nonumber \\
& z^v_i \in \{0,1\}\ \ \forall i \in N \mbox{ - bus voltage on/off variable} \\
& z^g_i \in \{0,1\}\ \ \forall i \in G \mbox{ - generator on/off variable} \\
& z^b_i \in \{0,1\}\ \ \forall i \in B\mbox{ - storage on/off variable} \\
& z^d_i \in \{0,1\}\ \ \forall i \in L \mbox{ - load on/off variable} \\
& z^s_i \in \{0,1\}\ \ \forall i \in H \mbox{ - shunt on/off variable} \\
& z^{sw}_i \in \{0,1\}\ \ \forall i \in S \mbox{ - switch open/closed variable}
\end{align}
```

## OSW/MLD Objective

```math
\begin{align}
\mbox{minimize: } & \nonumber \\
& \sum_{\substack{i\in N,c\in C}}{10 \left (1-z^v_i \right )} + \nonumber \\
& \sum_{\substack{i\in L,c\in C}}{10 \omega_{i,c}\left |\Re{\left (S^d_i\right )}\right |\left ( 1-z^d_i \right ) } + \nonumber \\
& \sum_{\substack{i\in H,c\in C}}{\left | \Re{\left (S^s_i \right )}\right | \left (1-z^s_i \right ) } + \nonumber \\
& \sum_{\substack{i\in G,c\in C}}{\Delta^g_i } + \nonumber \\
& \sum_{\substack{i\in B,c\in C}}{\Delta^b_i}  + \nonumber \\
& \sum_{\substack{i\in S}}{\Delta^{sw}_i}
\end{align}
```

where

```math
\begin{align}
\Delta^g_i &>= \left [\Re{\left (S^g_{i}(0) \right )} - \Re{\left (S^g_i \right )} \right ] \\
\Delta^g_i &>= -\left [\Re{\left (S^g_{i}(0) \right )} - \Re{\left (S^g_i \right )} \right ] \\
\Delta^b_i &>= \left [\Re{\left (S^b_{i}(0) \right )} - \Re{\left (S^b_i \right )} \right ] \\
\Delta^b_i &>= -\left [\Re{\left (S^b_{i}(0) \right )} - \Re{\left (S^b_i \right )} \right ]
\end{align}
```

## OSW/MLD Constraints

```math
\begin{align}
\mbox{subject to: } & \nonumber \\
& z^v_i v^l_{i,c} \leq \left | V_{i,c} \right | \leq z_i^v v^u_{i,c}\ \ \forall i \in N,\forall c \in C \\
& z^g_i S^{gl}_{i,c} \leq S^g_{i,c} \leq z^g_i S^{gu}_{i,c}\ \ \forall i \in G,\forall c \in C \\
& \sum_{\substack{k\in G_i,c\in C}} S^g_{k,c} - \sum_{\substack{k\in L_i,c\in C}} z^d_k S^d_{k,c}- \sum_{\substack{k\in H_i,c\in C}} z^s_k Y^s_{k,c}&& \left | V_{i,c} \right |^2 = \nonumber \\
& \sum_{\substack{(i,j)\in E_i\cup E_i^R,c\in C}} S_{ij,c}\ \forall i \in N \\
& z^{sw}_i \leq z^d_b\ \forall i \in S,\forall b \in L \\
& z^{sw}_i \geq 0\ \forall i \in S \\
& S^{sw}_i \leq S^{swu} z^{sw}_i\ \forall i \in S \\
& S^{sw}_i \geq -S^{swu} z^{sw}_i\ \forall i \in S \\
& V^{fr}_{i,c} - V^{to}_{i,c} \leq v^u_{i,c} \left ( 1 - z^{sw}_i \right )\ \forall i \in S,\forall c \in C \\
& V^{fr}_{i,c} - V^{to}_{i,c} \geq -v^u_{i,c} \left ( 1 - z^{sw}_i \right )\ \forall i \in S,\forall c \in C
\end{align}
```
