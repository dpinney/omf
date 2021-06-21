"KCL for load shed problem with transformers (AbstractWForms)"
function constraint_mc_power_balance_shed(
    pm::PMD.LPUBFDiagModel, nw::Int, i::Int,
    terminals::Vector{Int}, grounded::Vector{Bool},
    bus_arcs::Vector{Tuple{Tuple{Int,Int,Int},Vector{Int}}},
    bus_arcs_sw::Vector{Tuple{Tuple{Int,Int,Int},Vector{Int}}},
    bus_arcs_trans::Vector{Tuple{Tuple{Int,Int,Int},Vector{Int}}},
    bus_gens::Vector{Tuple{Int,Vector{Int}}},
    bus_storage::Vector{Tuple{Int,Vector{Int}}},
    bus_loads::Vector{Tuple{Int,Vector{Int}}},
    bus_shunts::Vector{Tuple{Int,Vector{Int}}})
    w        = PMD.var(pm, nw, :w, i)
    p        = get(PMD.var(pm, nw),    :p, Dict()); PMD._PM._check_var_keys(p, bus_arcs, "active power", "branch")
    q        = get(PMD.var(pm, nw),    :q, Dict()); PMD._PM._check_var_keys(q, bus_arcs, "reactive power", "branch")
    pg       = get(PMD.var(pm, nw),   :pg, Dict()); PMD._PM._check_var_keys(pg, bus_gens, "active power", "generator")
    qg       = get(PMD.var(pm, nw),   :qg, Dict()); PMD._PM._check_var_keys(qg, bus_gens, "reactive power", "generator")
    ps       = get(PMD.var(pm, nw),   :ps, Dict()); PMD._PM._check_var_keys(ps, bus_storage, "active power", "storage")
    qs       = get(PMD.var(pm, nw),   :qs, Dict()); PMD._PM._check_var_keys(qs, bus_storage, "reactive power", "storage")
    psw      = get(PMD.var(pm, nw),  :psw, Dict()); PMD._PM._check_var_keys(psw, bus_arcs_sw, "active power", "switch")
    qsw      = get(PMD.var(pm, nw),  :qsw, Dict()); PMD._PM._check_var_keys(qsw, bus_arcs_sw, "reactive power", "switch")
    pt       = get(PMD.var(pm, nw),   :pt, Dict()); PMD._PM._check_var_keys(pt, bus_arcs_trans, "active power", "transformer")
    qt       = get(PMD.var(pm, nw),   :qt, Dict()); PMD._PM._check_var_keys(qt, bus_arcs_trans, "reactive power", "transformer")
    z_demand = PMD.var(pm, nw, :z_demand)
    z_shunt  = PMD.var(pm, nw, :z_shunt)

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
            - sum(PMD.ref(pm, nw, :load, l, "pd")[findfirst(isequal(t), conns)] * z_demand[l] for (l, conns) in bus_loads if t in conns)
            # - sum(z_shunt[sh] *(w[t] * PMD.diag(Gt')[idx]) for (sh, conns) in bus_shunts if t in conns)
        )
        push!(cstr_p, cp)
        cq = PMD.JuMP.@constraint(pm.model,
              sum(q[a][t] for (a, conns) in bus_arcs if t in conns)
            + sum(qsw[a_sw][t] for (a_sw, conns) in bus_arcs_sw if t in conns)
            + sum(qt[a_trans][t] for (a_trans, conns) in bus_arcs_trans if t in conns)
            ==
            sum(qg[g][t] for (g, conns) in bus_gens if t in conns)
            - sum(qs[s][t] for (s, conns) in bus_storage if t in conns)
            - sum(PMD.ref(pm, nw, :load, l, "qd")[findfirst(isequal(t), conns)]*z_demand[l] for (l, conns) in bus_loads if t in conns)
            # + sum(z_shunt[sh] * (w[t] * PMD.diag(Bt')[idx]) for (sh, conns) in bus_shunts if t in conns)
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


""
function PowerModelsDistribution.constraint_mc_switch_power_on_off(pm::PMD.LPUBFDiagModel, nw::Int, f_idx::Tuple{Int,Int,Int}; relax::Bool=false)
    i, f_bus, t_bus = f_idx

    psw = PMD.var(pm, nw, :psw, f_idx)
    qsw = PMD.var(pm, nw, :qsw, f_idx)

    z = PMD.var(pm, nw, :switch_state, i)

    connections = PMD.ref(pm, nw, :switch, i)["f_connections"]

    rating = get(PMD.ref(pm, nw, :switch, i), "rate_a", fill(1e-2, length(connections)))

    for (idx, c) in enumerate(connections)
        if relax
            PMD.JuMP.@constraint(pm.model, psw[c] <=  rating[idx] * z)
            PMD.JuMP.@constraint(pm.model, psw[c] >= -rating[idx] * z)
            PMD.JuMP.@constraint(pm.model, qsw[c] <=  rating[idx] * z)
            PMD.JuMP.@constraint(pm.model, qsw[c] >= -rating[idx] * z)
        else
            PMD.JuMP.@constraint(pm.model, !z => {psw[c] == 0.0})
            PMD.JuMP.@constraint(pm.model, !z => {qsw[c] == 0.0})
        end
    end
end


""
function PowerModelsDistribution.constraint_mc_switch_state_on_off(pm::PMD.LPUBFDiagModel, nw::Int, i::Int, f_bus::Int, t_bus::Int, f_connections::Vector{Int}, t_connections::Vector{Int}; relax::Bool=false)
    w_fr = PMD.var(pm, nw, :w, f_bus)
    w_to = PMD.var(pm, nw, :w, t_bus)

    z = PMD.var(pm, nw, :switch_state, i)

    for (fc, tc) in zip(f_connections, t_connections)
        if relax
            M = 0.2
            PMD.JuMP.@constraint(pm.model, w_fr[fc] - w_to[tc] <=  M * (1-z))
            PMD.JuMP.@constraint(pm.model, w_fr[fc] - w_to[tc] >= -M * (1-z))
        else
            PMD.JuMP.@constraint(pm.model, z => {w_fr[fc] == w_to[tc]})
        end
    end
end
