"""
    constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default)

max switching actions per timestep constraint
"""
function constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default)
    constraint_switch_state_max_actions(pm, nw)
end


"""
    constraint_load_block_isolation(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, relax::Bool=true)

constraint to ensure that load blocks are properly isolated by opening switches
"""
function constraint_load_block_isolation(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, relax::Bool=true)
    constraint_load_block_isolation(pm, nw; relax=relax)
end
