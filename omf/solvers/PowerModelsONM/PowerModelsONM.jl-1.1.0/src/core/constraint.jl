@doc raw"""
    constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel, nw::Int)

max actions per timestep switch constraint

```math
\sum_{\substack{i\in S}}{\Delta^{sw}_i} \leq z^{swu}
```
"""
function constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel, nw::Int)
    max_switch_actions = PMD.ref(pm, nw, :max_switch_actions)

    delta_switch_states = Dict(l => PMD.JuMP.@variable(pm.model, base_name="$(nw)_delta_sw_state_$(l)", start=0) for l in PMD.ids(pm, nw, :switch_dispatchable))
    for (l, dsw) in delta_switch_states
        PMD.JuMP.@constraint(pm.model, dsw >= PMD.var(pm, nw, :switch_state, l) * (1 - PMD.JuMP.start_value(PMD.var(pm, nw, :switch_state, l))))
        PMD.JuMP.@constraint(pm.model, dsw >= PMD.var(pm, nw, :switch_state, l) * (PMD.JuMP.start_value(PMD.var(pm, nw, :switch_state, l)) - 1))
    end

    if max_switch_actions < Inf
        PMD.JuMP.@constraint(pm.model, sum(dsw for (l, dsw) in delta_switch_states) <= max_switch_actions)
    end
end


@doc raw"""
    constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel, nw_1::Int, nw_2::Int)

max actions per timestep switch constraint for multinetwork formulations

```math
\sum_{\substack{i\in S}}{\Delta^{sw}_i} \leq z^{swu}
```
"""
function constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel, nw_1::Int, nw_2::Int)
    max_switch_actions = PMD.ref(pm, nw_2, :max_switch_actions)

    delta_switch_states = Dict(l => PMD.JuMP.@variable(pm.model, base_name="$(nw_2)_delta_sw_state_$(l)", start=0) for l in PMD.ids(pm, nw_2, :switch_dispatchable))
    for (l, dsw) in delta_switch_states
        PMD.JuMP.@constraint(pm.model, dsw >= PMD.var(pm, nw_2, :switch_state, l) * (1 - PMD.var(pm, nw_1, :switch_state, l)))
        PMD.JuMP.@constraint(pm.model, dsw >= PMD.var(pm, nw_2, :switch_state, l) * (PMD.var(pm, nw_1, :switch_state, l) - 1))
    end

    if max_switch_actions < Inf
        PMD.JuMP.@constraint(pm.model, sum(dsw for (l, dsw) in delta_switch_states) <= max_switch_actions)
    end
end


@doc raw"""
    constraint_block_isolation(pm::PMD.LPUBFDiagModel, nw::Int; relax::Bool=false)

constraint to ensure that blocks get properly isolated by open switches by comparing the states of
two neighboring blocks. If the neighboring block indicators are not either both 0 or both 1, the switch
between them should be OPEN (0)

```math
\begin{align}
& (z^{bl}_{fr}_{i} - z^{bl}_{to}_{i}) \leq  z^{sw}_{i}\ \forall i in S \\
& (z^{bl}_{fr}_{i} - z^{bl}_{fr}_{i}) \geq -z^{sw}_{i}\ \forall i in S
\end{align}

where $$z^{bl}_{fr}_{i}$$ and $$z^{bl}_{to}_{i}$$ are the indicator variables for the blocks on
either side of switch $$i$$.
```
"""
function constraint_block_isolation(pm::PMD.AbstractUnbalancedPowerModel, nw::Int; relax::Bool=false)
    for (s, switch) in PMD.ref(pm, nw, :switch_dispatchable)
        z_block_fr = PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :bus_block_map, switch["f_bus"]))
        z_block_to = PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :bus_block_map, switch["t_bus"]))

        z_switch = PMD.var(pm, nw, :switch_state, s)
        if relax
            PMD.JuMP.@constraint(pm.model,  (z_block_fr - z_block_to) <=  (1-z_switch))
            PMD.JuMP.@constraint(pm.model,  (z_block_fr - z_block_to) >= -(1-z_switch))
        else # "indicator" constraint
            PMD.JuMP.@constraint(pm.model, z_switch => {z_block_fr == z_block_to})
        end
    end

    for (b, block) in PMD.ref(pm, nw, :blocks)
        z_block = PMD.var(pm, nw, :z_block, b)
        n_gen = length(PMD.ref(pm, nw, :block_gens)) + length(PMD.ref(pm, nw, :block_storages))

        PMD.JuMP.@constraint(pm.model, z_block <= n_gen + sum(PMD.var(pm, nw, :switch_state, s) for s in PMD.ids(pm, nw, :block_switches) if s in PMD.ids(pm, nw, :switch_dispatchable)))
    end
end
