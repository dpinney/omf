"""
    get_timestep_device_actions!(args::Dict{String,<:Any})::Vector{Dict{String,Any}}

Gets the device actions at every timestep using [`get_timestep_device_actions`](@ref get_timestep_device_actions)
and applies it in place to args, for use in [`entrypoint`](@ref entrypoint).
"""
function get_timestep_device_actions!(args::Dict{String,<:Any})::Vector{Dict{String,Any}}
    args["output_data"]["Device action timeline"] = get_timestep_device_actions(args["network"], args["optimal_switching_results"])
end


"""
    get_timestep_device_actions(network::Dict{String,<:Any}, mld_results::Dict{String,<:Any})::Vector{Dict{String,Any}}

From the multinetwork `network`, determines the switch configuration at each timestep. If the switch does not exist
in `mld_results`, the state will default back to the state given in the original network. This could happen if the switch
is not dispatchable, and therefore `state` would not be expected in the results.

Will output Vector{Dict} where each Dict will contain `"Switch configurations"`, which is a Dict with switch names as keys,
and the switch state, `"open"` or `"closed"` as values, and `"Shedded loads"`, which is a list of load names that have been
shed at that timestep.
"""
function get_timestep_device_actions(network::Dict{String,<:Any}, mld_results::Dict{String,<:Any})::Vector{Dict{String,Any}}
    device_action_timeline = Dict{String,Any}[]

    for n in sort([parse(Int, k) for k in keys(network["nw"])])
        _out = Dict{String,Any}(
            "Switch configurations" => Dict{String,String}(),
            "Shedded loads" => String[],
        )
        for (id, switch) in get(network["nw"]["$n"], "switch", Dict())
            state = lowercase(string(switch["state"]))
            if haskey(mld_results, "$n") && haskey(mld_results["$n"], "solution") && haskey(mld_results["$n"]["solution"], "switch") && haskey(mld_results["$n"]["solution"]["switch"], id) && haskey(mld_results["$n"]["solution"]["switch"][id], "state")
                state = lowercase(string(mld_results["$n"]["solution"]["switch"][id]["state"]))
            end
            _out["Switch configurations"][id] = state
        end

        for (id, load) in get(network["nw"]["$n"], "load", Dict())
            if haskey(mld_results, "$n") && haskey(mld_results["$n"], "solution") && haskey(mld_results["$n"]["solution"], "load") && haskey(mld_results["$n"]["solution"]["load"], id) && haskey(mld_results["$n"]["solution"]["load"][id], "status")
                if round(mld_results["$n"]["solution"]["load"][id]["status"]) ≉ 1
                    push!(_out["Shedded loads"], id)
                end
            end
        end

        push!(device_action_timeline, _out)
    end

    return device_action_timeline
end


"""
    get_timestep_switch_changes!(args::Dict{String,<:Any})::Vector{Vector{String}}

Gets the switch changes via [`get_timestep_switch_changes`](@ref get_timestep_switch_changes)
and applies it in-place to args, for use with [`entrypoint`](@ref entrypoint)
"""
function get_timestep_switch_changes!(args::Dict{String,<:Any})::Vector{Vector{String}}
    args["output_data"]["Switch changes"] = get_timestep_switch_changes(args["network"])
end


"""
    get_timestep_switch_changes(network::Dict{String,<:Any})::Vector{Vector{String}}

Gets a list of switches whose state has changed between timesteps (always expect the first timestep to be an empty list).
This expects the solutions from the MLD problem to have been merged into `network`
"""
function get_timestep_switch_changes(network::Dict{String,<:Any})::Vector{Vector{String}}
    switch_changes = Vector{String}[]

    _switch_states = Dict(n => Dict(id => switch["state"] for (id, switch) in get(network["nw"][n], "switch", Dict())) for n in keys(network["nw"]))
    ns = sort([parse(Int, i) for i in keys(network["nw"])])
    for (i,n) in enumerate(ns)
        _switch_changes = String[]
        if i > 1
            _prev_states = _switch_states["$(ns[i-1])"]
            for (id, state) in _switch_states["$n"]
                if state != _prev_states[id]
                    push!(_switch_changes, id)
                end
            end
        end
        push!(switch_changes, _switch_changes)
    end

    return switch_changes
end
