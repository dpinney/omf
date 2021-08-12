"helper function to update switch settings from a solution"
function _update_switch_settings!(data::Dict{String,<:Any}, solution::Dict{String,<:Any})
    for (id, switch) in get(solution, "switch", Dict{String,Any}())
        if haskey(switch, "state")
            data["switch"][id]["state"] = switch["state"]
        end
    end
end


"helper function to update storage capacity for the next subnetwork based on a solution"
function _update_storage_capacity!(data::Dict{String,<:Any}, solution::Dict{String,<:Any})
    for (i, strg) in get(solution, "storage", Dict())
        data["storage"][i]["_energy"] = deepcopy(data["storage"][i]["energy"])
        data["storage"][i]["energy"] = strg["se"]
    end
end


"""
    apply_switch_solutions!(network::Dict{String,<:Any}, optimal_switching_results::Dict{String,<:Any})::Dict{String,Any}

Updates a multinetwork `network` in-place with the results from optimal switching `optimal_switching_results`.

Used when not using the in-place version of [`optimize_switches!`](@ref optimize_switches!).
"""
function apply_switch_solutions!(network::Dict{String,<:Any}, optimal_switching_results::Dict{String,<:Any})::Dict{String,Any}
    network = apply_switch_solutions(network, optimal_switching_results)
end


"""
    apply_switch_solutions(network::Dict{String,<:Any}, optimal_switching_results::Dict{String,<:Any})::Dict{String,Any}

Creates a copy of the `network` with the solution copied in from `optimal_switching_results`
"""
function apply_switch_solutions(network::Dict{String,<:Any}, optimal_switching_results::Dict{String,<:Any})::Dict{String,Any}
    mn_data = deepcopy(network)
    for (n,nw) in mn_data["nw"]
        _update_switch_settings!(nw, get(get(optimal_switching_results, n, Dict{String,Any}()), "solution", Dict{String,Any}()))
        _update_storage_capacity!(nw, get(get(optimal_switching_results, n, Dict{String,Any}()), "solution", Dict{String,Any}()))
    end
    return mn_data
end
