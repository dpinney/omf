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
    nw_ids = sort(collect(PMD.nw_ids(pm)))

    for (i, n) in enumerate(nw_ids)
        nw_ref = PMD.ref(pm, n)

        PMD.var(pm, n)[:delta_sw_state] = PMD.JuMP.@variable(
            pm.model,
            [i in PMD.ids(pm, n, :switch_dispatchable)],
            base_name="$(n)_$(i)_delta_sw_state",
            start = 0
        )

        for (s,switch) in nw_ref[:switch_dispatchable]
            z_switch = PMD.var(pm, n, :switch_state, s)
            if i == 1
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_sw_state, s) >=  (PMD.JuMP.start_value(z_switch) - z_switch))
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_sw_state, s) >= -(PMD.JuMP.start_value(z_switch) - z_switch))
            else  # multinetwork
                z_switch_prev = PMD.var(pm, nw_ids[i-1], :switch_state, s)
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_sw_state, s) >=  (z_switch_prev - z_switch))
                PMD.JuMP.@constraint(pm.model, PMD.var(pm, n, :delta_sw_state, s) >= -(z_switch_prev - z_switch))
            end
        end
    end

    # weight for discouraging switch state changes should be an order of magnitude
    # smaller than the smallest block weight (to ensure all blocks get restored)
    Wdsw = Dict(n => minimum(filter(x->x==0,collect(values(PMD.ref(pm, n, :block_weights))))) for n in PMD.nw_ids(pm))

    PMD.JuMP.@objective(pm.model, Min,
        sum(
            sum( 1e-2 * sum(gen["cost"][1] * PMD.var(pm, n, :pg, i)[c] + gen["cost"][2] for c in gen["connections"]) for (i,gen) in nw_ref[:gen]) +
            sum( 1e3  * PMD.ref(pm, n, :block_weights, i)*(1-PMD.var(pm, n, :z_block, i)) for (i,block) in nw_ref[:blocks]) +
            sum( 1e-1  * PMD.ref(pm, n, :switch_scores, l)*(1-PMD.var(pm, n, :switch_state, l)) for l in PMD.ids(pm, n, :switch_dispatchable) ) +
            sum( 1e-4 * Wdsw[n] * sum(PMD.var(pm, n, :delta_sw_state, l)) for l in PMD.ids(pm, n, :switch_dispatchable))
        for (n, nw_ref) in PMD.nws(pm))
    )
end
