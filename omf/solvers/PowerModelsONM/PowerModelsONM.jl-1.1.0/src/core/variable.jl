"""
    variable_mc_block_indicator(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, relax::Bool=false, report::Bool=true)

create variables for block status by load block
"""
function variable_mc_block_indicator(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, relax::Bool=false, report::Bool=true)
    if relax
        z_block = PMD.var(pm, nw)[:z_block] = PMD.JuMP.@variable(pm.model,
            [i in PMD.ids(pm, nw, :blocks)], base_name="$(nw)_z_block",
            lower_bound = 0,
            upper_bound = 1,
            start = 0
        )
    else
        z_block = PMD.var(pm, nw)[:z_block] = PMD.JuMP.@variable(pm.model,
            [i in PMD.ids(pm, nw, :blocks)], base_name="$(nw)_z_block",
            binary = true,
            start = 0
        )
    end

    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :bus,     :status, PMD.ids(pm, nw, :bus),     Dict{Int,Any}(i => PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :bus_block_map, i))     for i in PMD.ids(pm, nw, :bus)))
    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :load,    :status, PMD.ids(pm, nw, :load),    Dict{Int,Any}(i => PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :load_block_map, i))    for i in PMD.ids(pm, nw, :load)))
    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :shunt,   :status, PMD.ids(pm, nw, :shunt),   Dict{Int,Any}(i => PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :shunt_block_map, i))   for i in PMD.ids(pm, nw, :shunt)))
    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :gen,     :status, PMD.ids(pm, nw, :gen),     Dict{Int,Any}(i => PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :gen_block_map, i))     for i in PMD.ids(pm, nw, :gen)))
    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :storage, :status, PMD.ids(pm, nw, :storage), Dict{Int,Any}(i => PMD.var(pm, nw, :z_block, PMD.ref(pm, nw, :storage_block_map, i)) for i in PMD.ids(pm, nw, :storage)))
end


"""
    variable_mc_switch_fixed(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, report::Bool=false)

Fixed switches set to constant values for multinetwork formulation (we need all switches)
"""
function variable_mc_switch_fixed(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, report::Bool=false)
    dispatchable_switches = collect(PMD.ids(pm, nw, :switch_dispatchable))
    fixed_switches = [i for i in PMD.ids(pm, nw, :switch) if i ∉ dispatchable_switches]

    for i in fixed_switches
        PMD.var(pm, nw, :switch_state)[i] = PMD.ref(pm, nw, :switch, i, "state")
    end

    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :switch, :status, fixed_switches, Dict{Int,Any}(i => PMD.var(pm, nw, :switch_state, i) for i in fixed_switches))
end


"switch state (open/close) variables"
function variable_mc_switch_state(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, report::Bool=true, relax::Bool=false)
    if relax
        state = PMD.var(pm, nw)[:switch_state] = Dict{Int,Any}(l => PMD.JuMP.@variable(
            pm.model,
            base_name="$(nw)_switch_state_$(l)",
            lower_bound = 0,
            upper_bound = 1,
            start = PMD.comp_start_value(PMD.ref(pm, nw, :switch, l), "state_start", get(PMD.ref(pm, nw, :switch, l), "state", 0))
        ) for l in PMD.ids(pm, nw, :switch_dispatchable))
    else
        state = PMD.var(pm, nw)[:switch_state] = Dict{Int,Any}(l => PMD.JuMP.@variable(
            pm.model,
            base_name="$(nw)_switch_state_$(l)",
            binary = true,
            start = PMD.comp_start_value(PMD.ref(pm, nw, :switch, l), "state_start", get(PMD.ref(pm, nw, :switch, l), "state", 0))
        ) for l in PMD.ids(pm, nw, :switch_dispatchable))
    end

    report && PMD._IM.sol_component_value(pm, PMD.pmd_it_sym, nw, :switch, :state, PMD.ids(pm, nw, :switch_dispatchable), state)
end
