@doc raw"""
    constraint_mc_switch_state_on_off(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, f_bus::Int, t_bus::Int, f_connections::Vector{Int}, t_connections::Vector{Int}; relax::Bool=false)

Linear switch power on/off constraint for LPUBFDiagModel. If `relax`, an [indicator constraint](https://jump.dev/JuMP.jl/stable/manual/constraints/#Indicator-constraints) is used.

```math
\begin{align}
& w^{fr}_{i,c} - w^{to}_{i,c} \leq \left ( v^u_{i,c} \right )^2 \left ( 1 - z^{sw}_i \right )\ \forall i \in S,\forall c \in C \\
& w^{fr}_{i,c} - w^{to}_{i,c} \geq -\left ( v^u_{i,c}\right )^2 \left ( 1 - z^{sw}_i \right )\ \forall i \in S,\forall c \in C
\end{align}
```
"""
function PowerModelsDistribution.constraint_mc_switch_state_on_off(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, f_bus::Int, t_bus::Int, f_connections::Vector{Int}, t_connections::Vector{Int}; relax::Bool=false)
    w_fr = PMD.var(pm, nw, :w, f_bus)
    w_to = PMD.var(pm, nw, :w, t_bus)

    f_bus = PMD.ref(pm, nw, :bus, f_bus)
    t_bus = PMD.ref(pm, nw, :bus, t_bus)

    f_vmax = f_bus["vmax"][[findfirst(isequal(c), f_bus["terminals"]) for c in f_connections]]
    t_vmax = t_bus["vmax"][[findfirst(isequal(c), t_bus["terminals"]) for c in t_connections]]

    vmax = min.(fill(2.0, length(f_bus["vmax"])), f_vmax, t_vmax)

    z = PMD.var(pm, nw, :switch_state, i)

    for (idx, (fc, tc)) in enumerate(zip(f_connections, t_connections))
        if relax
            JuMP.@constraint(pm.model, w_fr[fc] - w_to[tc] <=  vmax[idx].^2 * (1-z))
            JuMP.@constraint(pm.model, w_fr[fc] - w_to[tc] >= -vmax[idx].^2 * (1-z))
        else
            JuMP.@constraint(pm.model, z => {w_fr[fc] == w_to[tc]})
        end
    end
end


@doc raw"""
    constraint_mc_switch_power_on_off(pm::PMD.LPUBFDiagModel, nw::Int, f_idx::Tuple{Int,Int,Int}; relax::Bool=false)

Linear switch power on/off constraint for LPUBFDiagModel. If `relax`, an [indicator constraint](https://jump.dev/JuMP.jl/stable/manual/constraints/#Indicator-constraints) is used.

```math
\begin{align}
& S^{sw}_{i,c} \leq S^{swu}_{i,c} z^{sw}_i\ \forall i \in S,\forall c \in C \\
& S^{sw}_{i,c} \geq -S^{swu}_{i,c} z^{sw}_i\ \forall i \in S,\forall c \in C
\end{align}
```
"""
function PowerModelsDistribution.constraint_mc_switch_power_on_off(pm::PMD.LPUBFDiagModel, nw::Int, f_idx::Tuple{Int,Int,Int}; relax::Bool=false)
    i, f_bus, t_bus = f_idx

    psw = PMD.var(pm, nw, :psw, f_idx)
    qsw = PMD.var(pm, nw, :qsw, f_idx)

    z = PMD.var(pm, nw, :switch_state, i)

    connections = PMD.ref(pm, nw, :switch, i)["f_connections"]

    switch = PMD.ref(pm, nw, :switch, i)

    rating = min.(fill(100.0, length(connections)), PMD._calc_branch_power_max_frto(switch, PMD.ref(pm, nw, :bus, f_bus), PMD.ref(pm, nw, :bus, t_bus))...)

    for (idx, c) in enumerate(connections)
        if relax
            JuMP.@constraint(pm.model, psw[c] <=  rating[idx] * z)
            JuMP.@constraint(pm.model, psw[c] >= -rating[idx] * z)
            JuMP.@constraint(pm.model, qsw[c] <=  rating[idx] * z)
            JuMP.@constraint(pm.model, qsw[c] >= -rating[idx] * z)
        else
            JuMP.@constraint(pm.model, !z => {psw[c] == 0.0})
            JuMP.@constraint(pm.model, !z => {qsw[c] == 0.0})
        end
    end
end
