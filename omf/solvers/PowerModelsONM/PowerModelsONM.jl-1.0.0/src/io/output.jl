"""
    initialize_output(args::Dict{String,<:Any})::Dict{String,Any}

Initializes the empty data structure for "output_data"
"""
function initialize_output(args::Dict{String,<:Any})::Dict{String,Any}
    _deepcopy_args!(args)

    Dict{String,Any}(
        "Runtime arguments" => deepcopy(args["raw_args"]),
        "Simulation time steps" => Any[],
        "Load served" => Dict{String,Any}(
            "Feeder load (%)" => Real[],
            "Microgrid load (%)" => Real[],
            "Bonus load via microgrid (%)" => Real[],
        ),
        "Generator profiles" => Dict{String,Any}(
            "Grid mix (kW)" => Real[],
            "Solar DG (kW)" => Real[],
            "Energy storage (kW)" => Real[],
            "Diesel DG (kW)" => Real[],
        ),
        "Voltages" => Dict{String,Any}(
            "Min voltage (p.u.)" => Real[],
            "Mean voltage (p.u.)" => Real[],
            "Max voltage (p.u.)" => Real[],
        ),
        "Storage SOC (%)" => Real[],
        "Device action timeline" => Dict{String,Any}[],
        "Powerflow output" => Dict{String,Any}[],
        "Additional statistics" => Dict{String,Any}(),
        "Events" => Dict{String,Any}[],
        "Fault currents" => Dict{String,Any}[],
        "Small signal stable" => Bool[],
        "Runtime timestamp" => "$(Dates.now())",
    )
end


"""
    write_json(file::String, data::Dict{String,<:Any}; indent::Union{Int,Missing}=missing)

Write JSON `data` to `file`. If `!ismissing(indent)`, JSON will be pretty-formatted with `indent`
"""
function write_json(file::String, data::Dict{String,<:Any}; indent::Union{Int,Missing}=missing)
    open(file, "w") do io
        if ismissing(indent)
            JSON.print(io, data)
        else
            JSON.print(io, data, indent)
        end
    end
end


"""
    initialize_output!(args::Dict{String,<:Any})::Dict{String,Any}

Initializes the output data strucutre inside of the args dict at "output_data"
"""
function initialize_output!(args::Dict{String,<:Any})::Dict{String,Any}
    args["output_data"] = initialize_output(args)
end


"""
    analyze_results!(args::Dict{String,<:Any})::Dict{String,Any}

Adds information and statistics to "output_data", including

- `"Runtime arguments"`: Copied from `args["raw_args"]`
- `"Simulation time steps"`: Copied from `values(args["network"]["mn_lookup"])`, sorted by multinetwork id
- `"Events"`: Copied from `args["raw_events"]`
- `"Voltages"`: [`get_timestep_voltage_statistics!`](@ref get_timestep_voltage_statistics!)
- `"Load served"`: [`get_timestep_load_served!`](@ref get_timestep_load_served!)
- `"Generator profiles"`: [`get_timestep_generator_profiles!`](@ref get_timestep_generator_profiles!)
- `"Storage SOC (%)"`: [`get_timestep_storage_soc!`](@ref get_timestep_storage_soc!)
- `"Powerflow output"`: [`get_timestep_dispatch!`](@ref get_timestep_dispatch!)
- `"Device action timeline"`: [`get_timestep_device_actions!`](@ref get_timestep_device_actions!)
- `"Switch changes"`: [`get_timestep_switch_changes!`](@ref get_timestep_switch_changes!)
- `"Small signal stability"`: [`get_timestep_stability!`](@ref get_timestep_stability!)
- `"Fault currents"`: [`get_timestep_fault_currents!`](@ref get_timestep_fault_currents!)
"""
function analyze_results!(args::Dict{String,<:Any})::Dict{String,Any}
    if !haskey(args, "output_data")
        initialize_output!(args)
    end

    args["output_data"]["Simulation time steps"] = [args["network"]["mn_lookup"]["$n"] for n in sort([parse(Int,i) for i in keys(args["network"]["mn_lookup"])]) ]
    args["output_data"]["Events"] = args["raw_events"]

    get_timestep_voltage_statistics!(args)

    get_timestep_load_served!(args)
    get_timestep_generator_profiles!(args)
    get_timestep_storage_soc!(args)

    get_timestep_dispatch!(args)

    get_timestep_device_actions!(args)
    get_timestep_switch_changes!(args)

    get_timestep_stability!(args)

    get_timestep_fault_currents!(args)

    return args["output_data"]
end
