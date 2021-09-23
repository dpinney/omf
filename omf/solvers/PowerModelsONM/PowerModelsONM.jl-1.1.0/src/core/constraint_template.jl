"""
    constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default)

max switching actions per timestep constraint
"""
function constraint_switch_state_max_actions(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default)
    constraint_switch_state_max_actions(pm, nw)
end


"""
    constraint_block_isolation(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, relax::Bool=false)

constraint to ensure that blocks are properly isolated by open switches
"""
function constraint_block_isolation(pm::PMD.AbstractUnbalancedPowerModel; nw::Int=PMD.nw_id_default, relax::Bool=false)
    constraint_block_isolation(pm, nw; relax=relax)
end
