"""
    get_timestep_load_served!(args::Dict{String,<:Any})::Dict{String,Vector{Real}}

Gets Load served statistics in-place in args, for use in [`entrypoint`](@ref entrypoint),
using [`get_timestep_load_served`](@ref get_timestep_load_served).
"""
function get_timestep_load_served!(args::Dict{String,<:Any})::Dict{String,Vector{Real}}
    args["output_data"]["Load served"] = get_timestep_load_served(get(get(args, "optimal_dispatch_result", Dict{String,Any}()), "solution", Dict{String,Any}()), args["network"])
end


"""
    get_timestep_load_served(solution::Dict{String,<:Any}, network::Dict{String,<:Any})::Dict{String,Vector{Real}}

Returns Load statistics from an optimal dispatch `solution`, and compares to the base load (non-shedded) in `network`,
giving statistics for

- `"Feeder load (%)"`: How much load is the feeder supporting,
- `"Microgrid load (%)"`: How much load is(are) the microgrid(s) supporting,
- `"Bonus load via microgrid (%)"`: How much extra load is being supported.

## Note

Currently, because microgrids are not explicitly defined yet (see 'settings' file for initial implementation of microgrid tagging),
`"Bonus load via microgrid (%)"` only indicates how much charging is being performed on Storage.
"""
function get_timestep_load_served(solution::Dict{String,<:Any}, network::Dict{String,<:Any})::Dict{String,Vector{Real}}
    load_served = Dict{String,Vector{Real}}(
        "Feeder load (%)" => Real[],
        "Microgrid load (%)" => Real[],
        "Bonus load via microgrid (%)" => Real[],
    )

    for n in sort([parse(Int, i) for i in keys(get(solution, "nw", Dict()))])
        original_load = sum([sum(load["pd_nom"]) for (_,load) in network["nw"]["$n"]["load"]])

        feeder_served_load = !isempty(get(solution["nw"]["$n"], "voltage_source", Dict())) ? sum(Float64[sum(vs["pg"]) for (_,vs) in get(solution["nw"]["$n"], "voltage_source", Dict())]) : 0.0
        der_non_storage_served_load = !isempty(get(solution["nw"]["$n"], "generator", Dict())) || !isempty(get(solution["nw"]["$n"], "solar", Dict())) ? sum([sum(g["pg"]) for type in ["solar", "generator"] for (_,g) in get(solution["nw"]["$n"], type, Dict())]) : 0.0
        der_storage_served_load = !isempty(get(solution["nw"]["$n"], "storage", Dict())) ? sum([-sum(s["ps"]) for (_,s) in get(solution["nw"]["$n"], "storage", Dict())]) : 0.0

        # TODO once microgrids support tagging, redo load served statistics
        microgrid_served_load = (der_non_storage_served_load + der_storage_served_load) / original_load * 100
        _bonus_load = (microgrid_served_load - 100)

        push!(load_served["Feeder load (%)"], feeder_served_load / original_load * 100)  # CHECK
        push!(load_served["Microgrid load (%)"], microgrid_served_load)  # CHECK
        push!(load_served["Bonus load via microgrid (%)"], _bonus_load > 0 ? _bonus_load : 0.0)  # CHECK
    end
    return load_served
end


"""
    get_timestep_generator_profiles!(args::Dict{String,<:Any})::Dict{String,Vector{Real}}

Gets generator profile statistics for each timestep in-place in args, for use in [`entrypoint`](@ref entrypoint),
using [`get_timestep_generator_profiles`](@ref get_timestep_generator_profiles)
"""
function get_timestep_generator_profiles!(args::Dict{String,<:Any})::Dict{String,Vector{Real}}
    args["output_data"]["Generator profiles"] = get_timestep_generator_profiles(get(get(args, "optimal_dispatch_result", Dict{String,Any}()), "solution", Dict{String,Any}()))
end


"""
    get_timestep_generator_profiles(solution::Dict{String,<:Any})::Dict{String,Vector{Real}}

Returns statistics about the generator profiles from the optimal dispatch `solution`:

- `"Grid mix (kW)"`: how much power is from the substation
- `"Solar DG (kW)"`: how much power is from Solar PV DER
- `"Energy storage (kW)`: how much power is from Energy storage DER
- `"Diesel DG (kW)"`: how much power is from traditional generator DER
"""
function get_timestep_generator_profiles(solution::Dict{String,<:Any})::Dict{String,Vector{Real}}
    generator_profiles = Dict{String,Vector{Real}}(
        "Grid mix (kW)" => Real[],
        "Solar DG (kW)" => Real[],
        "Energy storage (kW)" => Real[],
        "Diesel DG (kW)" => Real[],
    )

    for n in sort([parse(Int, i) for i in keys(get(solution, "nw", Dict()))])
        push!(generator_profiles["Grid mix (kW)"], sum(Float64[sum(vsource["pg"]) for (_,vsource) in get(solution["nw"]["$n"], "voltage_source", Dict())]))
        push!(generator_profiles["Solar DG (kW)"], sum(Float64[sum(solar["pg"]) for (_,solar) in get(solution["nw"]["$n"], "solar", Dict())]))
        push!(generator_profiles["Energy storage (kW)"], sum(Float64[-sum(storage["ps"]) for (_,storage) in get(solution["nw"]["$n"], "storage", Dict())]))
        push!(generator_profiles["Diesel DG (kW)"], sum(Float64[sum(gen["pg"]) for (_,gen) in get(solution["nw"]["$n"], "generator", Dict())]))
    end

    return generator_profiles
end


"""
    get_timestep_storage_soc!(args::Dict{String,<:Any})::Vector{Real}

Gets storage energy remaining percentage for each timestep in-place in args, for use in [`entrypoint`](@ref entrypoint),
using [`get_timestep_storage_soc`](@ref get_timestep_storage_soc)
"""
function get_timestep_storage_soc!(args::Dict{String,<:Any})::Vector{Real}
    args["output_data"]["Storage SOC (%)"] = get_timestep_storage_soc(get(get(args, "optimal_dispatch_result", Dict{String,Any}()), "solution", Dict{String,Any}()), args["network"])
end


"""
    get_timestep_storage_soc(solution::Dict{String,<:Any}, network::Dict{String,<:Any})::Vector{Real}

Returns the storage state of charge, i.e., how much energy is remaining in all of the the energy storage DER
based on the optimal dispatch `solution`. Needs `network` to give percentage.
"""
function get_timestep_storage_soc(solution::Dict{String,<:Any}, network::Dict{String,<:Any})::Vector{Real}
    storage_soc = Real[]

    for n in sort([parse(Int, i) for i in keys(get(solution, "nw", Dict()))])
        if !isempty(get(solution["nw"]["$n"], "storage", Dict()))
            push!(storage_soc, 100.0 * sum(strg["se"] for strg in values(solution["nw"]["$n"]["storage"])) / sum(strg["energy_ub"] for strg in values(network["nw"]["$n"]["storage"])))
        else
            push!(storage_soc, NaN)
        end
    end

    return storage_soc
end
