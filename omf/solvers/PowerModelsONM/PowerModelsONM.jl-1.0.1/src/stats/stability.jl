"""
    get_timestep_stability!(args::Dict{String,<:Any})::Vector{Bool}

Gets the stability at each timestep and applies it in-place to args, for use in
[`entrypoint`](@ref entrypoint), using [`get_timestep_stability`](@ref get_timestep_stability)
"""
function get_timestep_stability!(args::Dict{String,<:Any})::Vector{Bool}
    args["output_data"]["Small signal stable"] = get_timestep_stability(get(args, "stability_results", Dict{String,Bool}()))
end


# TODO replace when stability features are more complex
"""
    get_timestep_stability(is_stable::Dict{String,Bool})::Vector{Bool}

This is a placeholder function that simple passes through the is_stable Vector
back, until the Stability feature gets more complex.
"""
get_timestep_stability(is_stable::Dict{String,Bool})::Vector{Bool} = Bool[is_stable["$n"] for n in sort([parse(Int,i) for i in keys(is_stable)])]
