"gen connections adaptation of min fuel cost polynomial linquad objective"
function objective_mc_min_fuel_cost_switch(pm::PMD._PM.AbstractPowerModel; report::Bool=true)
    gen_cost = Dict()
    for (n, nw_ref) in PMD.nws(pm)
        for (i,gen) in nw_ref[:gen]
            pg = sum( PMD.var(pm, n, :pg, i)[c] for c in gen["connections"] )

            if length(gen["cost"]) == 1
                gen_cost[(n,i)] = gen["cost"][1]
            elseif length(gen["cost"]) == 2
                gen_cost[(n,i)] = gen["cost"][1]*pg + gen["cost"][2]
            elseif length(gen["cost"]) == 3
                if gen["cost"][1] == 0
                    gen_cost[(n,i)] = gen["cost"][2]*pg + gen["cost"][3]
                else
                    gen_cost[(n,i)] = gen["cost"][1]*pg^2 + gen["cost"][2]*pg + gen["cost"][3]
                end
            else
                gen_cost[(n,i)] = 0.0
            end
        end
    end

    state_start = Dict(
        (n,l) => PMD.ref(pm, n, :switch, l, "state")
        for (n, nw_ref) in PMD.nws(pm) for l in PMD.ids(pm, n, :switch)
    )

    return PMD.JuMP.@objective(pm.model, Min,
        sum(
            sum( gen_cost[(n,i)] for (i,gen) in nw_ref[:gen] ) +
            sum( PMD.var(pm, n, :switch_state, l) for l in PMD.ids(pm, n, :switch_dispatchable)) +
            sum( (state_start[(n,l)] - PMD.var(pm, n, :switch_state, l)) * (round(state_start[(n,l)]) == 0 ? -1 : 1) for l in PMD.ids(pm, n, :switch_dispatchable))
        for (n, nw_ref) in PMD.nws(pm))
    )
end


"simplified minimum load delta objective (continuous load shed)"
function objective_mc_min_load_setpoint_delta_simple_switch(pm::PMD._PM.AbstractPowerModel)
    state_start = Dict(
        (n,l) => PMD.ref(pm, n, :switch, l, "state")
        for (n, nw_ref) in PMD.nws(pm) for l in PMD.ids(pm, n, :switch)
    )

    PMD.JuMP.@objective(pm.model, Min,
        sum(
            sum( ((1 - PMD.var(pm, n, :z_demand, i))) for i in keys(nw_ref[:load])) +
            sum( ((1 - PMD.var(pm, n, :z_shunt, i))) for (i,shunt) in nw_ref[:shunt]) +
            # sum( PMD.var(pm, n, :switch_state, l) for l in PMD.ids(pm, n, :switch_dispatchable)) +
            1e-3 * sum( (state_start[(n,l)] - PMD.var(pm, n, :switch_state, l)) * (round(state_start[(n,l)]) == 0 ? -1 : 1) for l in PMD.ids(pm, n, :switch_dispatchable))
        for (n, nw_ref) in PMD.nws(pm))
    )
end


"minimum load delta objective (continuous load shed) with storage"
function objective_mc_min_load_setpoint_delta_switch(pm::PMD._PM.AbstractPowerModel)
    for (n, nw_ref) in PMD.nws(pm)
        PMD.var(pm, n)[:delta_pg] = Dict(i => PMD.JuMP.@variable(pm.model,
                [c in PMD.ref(pm, n, :gen, i)["connections"]], base_name="$(n)_$(i)_delta_pg",
                start = 0.0) for i in PMD.ids(pm, n, :gen))

                PMD.var(pm, n)[:delta_ps] = Dict(i => PMD.JuMP.@variable(pm.model,
                [c in PMD.ref(pm, n, :storage, i)["connections"]], base_name="$(n)_$(i)_delta_ps",
                start = 0.0) for i in PMD.ids(pm, n, :storage))

        for (i, gen) in nw_ref[:gen]
            for (idx, c) in enumerate(gen["connections"])
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_pg, i)[c] >=  (gen["pg"][idx] - PMD.var(pm, n, :pg, i)[c]))
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_pg, i)[c] >= -(gen["pg"][idx] - PMD.var(pm, n, :pg, i)[c]))
            end
        end

        for (i, strg) in nw_ref[:storage]
            for (idx, c) in enumerate(strg["connections"])
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_ps, i)[c] >=  (strg["ps"][idx] - PMD.var(pm, n, :ps, i)[c]))
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_ps, i)[c] >= -(strg["ps"][idx] - PMD.var(pm, n, :ps, i)[c]))
            end
        end
    end

    state_start = Dict(
        (n,l) => PMD.ref(pm, n, :switch, l, "state")
        for (n, nw_ref) in PMD.nws(pm) for l in PMD.ids(pm, n, :switch)
    )

    w = Dict(n => Dict(i => 100*get(load, "weight", 1.0) for (i,load) in PMD.ref(pm, n, :load)) for n in PMD.nw_ids(pm))

    PMD.JuMP.@objective(pm.model, Min,
        sum(
            sum(                                                    10*(1 - PMD.var(pm, n, :z_voltage, i)) for  (i,bus) in   nw_ref[:bus]) +
            sum( w[n][i]*(1 - PMD.var(pm, n, :z_demand, i)) for  (i,load) in  nw_ref[:load]) +
            sum(          sum(abs.(shunt["gs"]) .+ abs.(shunt["bs"])) *(1 - PMD.var(pm, n,  :z_shunt, i)) for (i,shunt) in nw_ref[:shunt]) +
            sum( 1e-4 * sum(PMD.var(pm, n, :delta_pg, i)[c] for (idx,c) in enumerate(gen["connections"])) for (i,gen)  in nw_ref[:gen]) +
            sum( 1e-4 * sum(PMD.var(pm, n, :delta_ps, i)[c] for (idx,c) in enumerate(strg["connections"])) for (i,strg) in nw_ref[:storage]) +
            sum( 1e-3 * (state_start[(n,l)] - PMD.var(pm, n, :switch_state, l)) * (round(state_start[(n,l)]) ≈ 0 ? -1 : 1) for l in PMD.ids(pm, n, :switch_dispatchable))
        for (n, nw_ref) in PMD.nws(pm))
    )
end
