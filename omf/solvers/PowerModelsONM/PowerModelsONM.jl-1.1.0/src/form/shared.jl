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

    rating = min.(fill(1.0, length(connections)), PMD._calc_branch_power_max_frto(switch, PMD.ref(pm, nw, :bus, f_bus), PMD.ref(pm, nw, :bus, t_bus))...)

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


"KCL for load shed problem with transformers (AbstractWForms)"
function PowerModelsDistribution.constraint_mc_power_balance_shed(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, terminals::Vector{Int}, grounded::Vector{Bool}, bus_arcs::Vector{Tuple{Tuple{Int,Int,Int},Vector{Int}}}, bus_arcs_sw::Vector{Tuple{Tuple{Int,Int,Int},Vector{Int}}}, bus_arcs_trans::Vector{Tuple{Tuple{Int,Int,Int},Vector{Int}}}, bus_gens::Vector{Tuple{Int,Vector{Int}}}, bus_storage::Vector{Tuple{Int,Vector{Int}}}, bus_loads::Vector{Tuple{Int,Vector{Int}}}, bus_shunts::Vector{Tuple{Int,Vector{Int}}})
    w        = PMD.var(pm, nw, :w, i)
    p        = get(PMD.var(pm, nw),    :p, Dict()); PMD._check_var_keys(p, bus_arcs, "active power", "branch")
    q        = get(PMD.var(pm, nw),    :q, Dict()); PMD._check_var_keys(q, bus_arcs, "reactive power", "branch")
    pg       = get(PMD.var(pm, nw),   :pg, Dict()); PMD._check_var_keys(pg, bus_gens, "active power", "generator")
    qg       = get(PMD.var(pm, nw),   :qg, Dict()); PMD._check_var_keys(qg, bus_gens, "reactive power", "generator")
    ps       = get(PMD.var(pm, nw),   :ps, Dict()); PMD._check_var_keys(ps, bus_storage, "active power", "storage")
    qs       = get(PMD.var(pm, nw),   :qs, Dict()); PMD._check_var_keys(qs, bus_storage, "reactive power", "storage")
    psw      = get(PMD.var(pm, nw),  :psw, Dict()); PMD._check_var_keys(psw, bus_arcs_sw, "active power", "switch")
    qsw      = get(PMD.var(pm, nw),  :qsw, Dict()); PMD._check_var_keys(qsw, bus_arcs_sw, "reactive power", "switch")
    pt       = get(PMD.var(pm, nw),   :pt, Dict()); PMD._check_var_keys(pt, bus_arcs_trans, "active power", "transformer")
    qt       = get(PMD.var(pm, nw),   :qt, Dict()); PMD._check_var_keys(qt, bus_arcs_trans, "reactive power", "transformer")
    z_block = PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :bus_block_map, i))

    Gt, Bt = PMD._build_bus_shunt_matrices(pm, nw, terminals, bus_shunts)

    cstr_p = []
    cstr_q = []

    ungrounded_terminals = [(idx,t) for (idx,t) in enumerate(terminals) if !grounded[idx]]

    for (idx, t) in ungrounded_terminals
        cp = PMD.JuMP.@constraint(pm.model,
              sum(p[a][t] for (a, conns) in bus_arcs if t in conns)
            + sum(psw[a_sw][t] for (a_sw, conns) in bus_arcs_sw if t in conns)
            + sum(pt[a_trans][t] for (a_trans, conns) in bus_arcs_trans if t in conns)
            ==
            sum(pg[g][t] for (g, conns) in bus_gens if t in conns)
            - sum(ps[s][t] for (s, conns) in bus_storage if t in conns)
            - sum(PMD.ref(pm, nw, :load, l, "pd")[findfirst(isequal(t), conns)] * z_block for (l, conns) in bus_loads if t in conns)
            - sum((w[t] * PMD.LinearAlgebra.diag(Gt')[idx]) for (sh, conns) in bus_shunts if t in conns)
        )
        push!(cstr_p, cp)
        cq = PMD.JuMP.@constraint(pm.model,
              sum(q[a][t] for (a, conns) in bus_arcs if t in conns)
            + sum(qsw[a_sw][t] for (a_sw, conns) in bus_arcs_sw if t in conns)
            + sum(qt[a_trans][t] for (a_trans, conns) in bus_arcs_trans if t in conns)
            ==
            sum(qg[g][t] for (g, conns) in bus_gens if t in conns)
            - sum(qs[s][t] for (s, conns) in bus_storage if t in conns)
            - sum(PMD.ref(pm, nw, :load, l, "qd")[findfirst(isequal(t), conns)] * z_block for (l, conns) in bus_loads if t in conns)
            - sum((-w[t] * PMD.LinearAlgebra.diag(Bt')[idx]) for (sh, conns) in bus_shunts if t in conns)
        )
        push!(cstr_q, cq)
    end

    PMD.con(pm, nw, :lam_kcl_r)[i] = cstr_p
    PMD.con(pm, nw, :lam_kcl_i)[i] = cstr_q

    if PMD._IM.report_duals(pm)
        PMD.sol(pm, nw, :bus, i)[:lam_kcl_r] = cstr_p
        PMD.sol(pm, nw, :bus, i)[:lam_kcl_i] = cstr_q
    end
end


"on/off bus voltage magnitude squared constraint for relaxed formulations"
function PowerModelsDistribution.constraint_mc_bus_voltage_magnitude_sqr_on_off(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, vmin::Vector{<:Real}, vmax::Vector{<:Real})
    w = PMD.var(pm, nw, :w, i)
    z_block = PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :bus_block_map, i))

    terminals = PMD.ref(pm, nw, :bus, i)["terminals"]
    grounded = PMD.ref(pm, nw, :bus, i)["grounded"]

    for (idx,t) in [(idx,t) for (idx,t) in enumerate(terminals) if !grounded[idx]]
        if isfinite(vmax[idx])
            PMD.JuMP.@constraint(pm.model, w[t] <= vmax[idx]^2*z_block)
        end

        if isfinite(vmin[idx])
            PMD.JuMP.@constraint(pm.model, w[t] >= vmin[idx]^2*z_block)
        end
    end
end


"on/off constraint for generators"
function PowerModelsDistribution.constraint_mc_gen_power_on_off(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, connections::Vector{<:Int}, pmin::Vector{<:Real}, pmax::Vector{<:Real}, qmin::Vector{<:Real}, qmax::Vector{<:Real})
    pg = PMD.var(pm, nw, :pg, i)
    qg = PMD.var(pm, nw, :qg, i)
    z = PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :gen_block_map, i))

    for (idx, c) in enumerate(connections)
        if isfinite(pmax[idx])
            PMD.JuMP.@constraint(pm.model, pg[c] .<= pmax[idx].*z)
        end

        if isfinite(pmin[idx])
            PMD.JuMP.@constraint(pm.model, pg[c] .>= pmin[idx].*z)
        end

        if isfinite(qmax[idx])
            PMD.JuMP.@constraint(pm.model, qg[c] .<= qmax[idx].*z)
        end

        if isfinite(qmin[idx])
            PMD.JuMP.@constraint(pm.model, qg[c] .>= qmin[idx].*z)
        end
    end
end


"on/off constraint for storage"
function PowerModelsDistribution.constraint_mc_storage_on_off(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, connections::Vector{Int}, pmin::Vector{<:Real}, pmax::Vector{<:Real}, qmin::Vector{<:Real}, qmax::Vector{<:Real}, charge_ub, discharge_ub)
    z = PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :storage_block_map, i))
    ps = [PMD.var(pm, nw, :ps, i)[c] for c in connections]
    qs = [PMD.var(pm, nw, :qs, i)[c] for c in connections]

    PMD.JuMP.@constraint(pm.model, ps .<= z.*pmax)
    PMD.JuMP.@constraint(pm.model, ps .>= z.*pmin)

    PMD.JuMP.@constraint(pm.model, qs .<= z.*qmax)
    PMD.JuMP.@constraint(pm.model, qs .>= z.*qmin)
end

