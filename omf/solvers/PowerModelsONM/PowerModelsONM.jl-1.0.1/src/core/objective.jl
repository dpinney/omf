@doc raw"""
    objective_mc_min_load_setpoint_delta_switch(pm::PMD.AbstractUnbalancedPowerModel)

minimum load delta objective (continuous load shed) with storage

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
"""
function objective_mc_min_load_setpoint_delta_switch(pm::PMD.AbstractUnbalancedPowerModel)
    for (n, nw_ref) in PMD.nws(pm)
        PMD.var(pm, n)[:delta_pg] = Dict(
            i => PMD.JuMP.@variable(
                pm.model,
                [c in PMD.ref(pm, n, :gen, i)["connections"]],
                base_name="$(n)_$(i)_delta_pg",
                start = 0.0
            ) for i in PMD.ids(pm, n, :gen)
        )

        for (i, gen) in nw_ref[:gen]
            for (idx, c) in enumerate(gen["connections"])
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_pg, i)[c] >=  (gen["pg"][idx] - PMD.var(pm, n, :pg, i)[c]))
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_pg, i)[c] >= -(gen["pg"][idx] - PMD.var(pm, n, :pg, i)[c]))
            end
        end

        PMD.var(pm, n)[:delta_ps] = Dict(
            i => PMD.JuMP.@variable(
                pm.model,
                [c in PMD.ref(pm, n, :storage, i)["connections"]],
                base_name="$(n)_$(i)_delta_ps",
                start = 0.0
            ) for i in PMD.ids(pm, n, :storage)
        )

        for (i, strg) in nw_ref[:storage]
            for (idx, c) in enumerate(strg["connections"])
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_ps, i)[c] >=  (strg["ps"][idx] - PMD.var(pm, n, :ps, i)[c]))
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_ps, i)[c] >= -(strg["ps"][idx] - PMD.var(pm, n, :ps, i)[c]))
            end
        end

        PMD.var(pm, n)[:delta_sw_state] = PMD.JuMP.@variable(
            pm.model,
            [i in PMD.ids(pm, n, :switch_dispatchable)],
            base_name="$(n)_$(i)_delta_sw_state",
            start = 0
        )

        for (i,switch) in nw_ref[:switch_dispatchable]
            PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_sw_state, i) >=  (switch["state"] - PMD.var(pm, n, :switch_state, i)))
            PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_sw_state, i) >= -(switch["state"] - PMD.var(pm, n, :switch_state, i)))
        end
    end

    w = Dict(n => Dict(i => 100*get(load, "weight", 1.0) for (i,load) in PMD.ref(pm, n, :load)) for n in PMD.nw_ids(pm))

    PMD.JuMP.@objective(pm.model, Min,
        sum(
            sum(      10*(1 - PMD.var(pm, n, :z_voltage, i)) for  (i,bus) in   nw_ref[:bus]) +
            sum( w[n][i]*(1 - PMD.var(pm, n, :z_demand, i)) for  (i,load) in  nw_ref[:load]) +
            sum(         (1 - PMD.var(pm, n, :z_shunt, i)) for  (i,shunt) in nw_ref[:shunt]) +
            sum( 1e-4 * sum(PMD.var(pm, n, :delta_pg, i)[c] for (idx,c) in enumerate(gen["connections"])) for (i,gen)  in nw_ref[:gen]) +
            sum( 1e-4 * sum(PMD.var(pm, n, :delta_ps, i)[c] for (idx,c) in enumerate(strg["connections"])) for (i,strg) in nw_ref[:storage]) +
            sum( 1e-3 * sum(PMD.var(pm, n, :delta_sw_state, l)) for l in PMD.ids(pm, n, :switch_dispatchable))
        for (n, nw_ref) in PMD.nws(pm))
    )
end
