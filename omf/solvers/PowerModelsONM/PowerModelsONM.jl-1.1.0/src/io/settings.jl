"""
    parse_settings!(args::Dict{String,<:Any}; apply::Bool=true, validate::Bool=true)::Dict{String,Any}

Parses settings file specifed in runtime arguments in-place

Will attempt to convert depreciated runtime arguments to appropriate network settings
data structure.

## Validation

If `validate=true` (default), the parsed data structure will be validated against the latest [Settings Schema](@ref Settings-Schema).
"""
function parse_settings!(args::Dict{String,<:Any}; apply::Bool=true, validate::Bool=true)::Dict{String,Any}
    if !isempty(get(args, "settings", ""))
        if isa(args["settings"], String)
            args["settings"] = parse_settings(args["settings"]; validate=validate)
        end
    else
        args["settings"] = Dict{String,Any}()
    end

    # Handle depreciated command line arguments
    _convert_depreciated_runtime_args!(args, args["settings"], args["base_network"], length(args["network"]["nw"]))

    apply && apply_settings!(args)

    return args["settings"]
end


"helper function to convert depreciated runtime arguments to their appropriate network settings structure"
function _convert_depreciated_runtime_args!(runtime_args::Dict{String,<:Any}, settings::Dict{String,<:Any}, base_network::Dict{String,<:Any}, timesteps::Int)::Tuple{Dict{String,Any},Dict{String,Any}}
    haskey(runtime_args, "voltage-lower-bound") && _convert_voltage_bound_to_settings!(settings, base_network, "vm_lb", pop!(runtime_args, "voltage-lower-bound"))
    haskey(runtime_args, "voltage-upper-bound") && _convert_voltage_bound_to_settings!(settings, base_network, "vm_ub", pop!(runtime_args, "voltage-upper-bound"))
    haskey(runtime_args, "voltage-angle-difference") && _convert_to_settings!(settings, base_network, "line", "vad_lb", -runtime_args["voltage-angle-difference"])
    haskey(runtime_args, "voltage-angle-difference") && _convert_to_settings!(settings, base_network, "line", "vad_ub",  pop!(runtime_args, "voltage-angle-difference"))
    haskey(runtime_args, "clpu-factor") && _convert_to_settings!(settings, base_network, "load", "clpu_factor", pop!(runtime_args, "clpu-factor"); multiphase=false)
    if haskey(runtime_args, "timestep-hours")
        settings["time_elapsed"] = fill(pop!(runtime_args, "timestep-hours"), timesteps)
    end

    if haskey(runtime_args, "max-switch-actions")
        settings["max_switch_actions"] = fill(pop!(runtime_args, "max-switch-actions"), timesteps)
    end
    if haskey(runtime_args, "solver-tolerance")
        settings["nlp_solver_tol"] = pop!(runtime_args, "solver-tolerance")
    end

    return runtime_args, settings
end


"""
    parse_settings(settings_file::String; validate::Bool=true)::Dict{String,Any}

Parses network settings JSON file.

## Validation

If `validate=true` (default), the parsed data structure will be validated against the latest [Settings Schema](@ref Settings-Schema).
"""
function parse_settings(settings_file::String; validate::Bool=true)::Dict{String,Any}
    settings = JSON.parsefile(settings_file)

    if validate && !validate_settings(settings)
        error("'settings' file could not be validated")
    end

    PMD.correct_json_import!(settings)

    return settings
end


"""
    apply_settings!(args::Dict{String,Any})::Dict{String,Any}

Applies settings to the network
"""
function apply_settings!(args::Dict{String,Any})::Dict{String,Any}
    args["network"] = apply_settings(args["network"], get(args, "settings", Dict()))
end


"""
    apply_settings(network::Dict{String,<:Any}, settings::Dict{String,<:Any})::Dict{String,Any}

Applies `settings` to multinetwork `network`
"""
function apply_settings(network::Dict{String,<:Any}, settings::Dict{String,<:Any})::Dict{String,Any}
    mn_data = deepcopy(network)

    for (s, setting) in settings
        if s in PMD.pmd_eng_asset_types
            _apply_to_network!(mn_data, s, setting)
        elseif s in ["time_elapsed", "max_switch_actions"]
            for n in sort([parse(Int, i) for i in keys(mn_data["nw"])])
                mn_data["nw"]["$n"][s] = setting[n]
            end
        end
    end

    mn_data
end


"converts depreciated global settings, e.g. voltage-lower-bound, to the proper way to specify settings"
function _convert_to_settings!(settings::Dict{String,<:Any}, base_network::Dict{String,<:Any}, asset_type::String, property::String, value::Any; multiphase::Bool=true)
    if haskey(base_network, asset_type)
        if !haskey(settings, asset_type)
            settings[asset_type] = Dict{String,Any}()
        end

        for (id, asset) in base_network[asset_type]
            if !haskey(settings[asset_type], id)
                settings[asset_type][id] = Dict{String,Any}()
            end

            nphases = asset_type == "bus" ? length(asset["terminals"]) : asset_type in PMD._eng_edge_elements ? asset_type == "transformer" && haskey(asset, "bus") ? length(asset["connections"][1]) : length(asset["f_connections"]) : length(asset["connections"])

            settings[asset_type][id][property] = multiphase ? fill(value, nphases) : value
        end
    end
end


"helper function to convert"
function _convert_voltage_bound_to_settings!(settings::Dict{String,<:Any}, base_network::Dict{String,<:Any}, bound_name::String, bound_value::Real)
    if !haskey(settings, "bus")
        settings["bus"] = Dict{String,Any}()
    end

    bus_vbase, line_vbase = PMD.calc_voltage_bases(base_network, base_network["settings"]["vbases_default"])
    for (id,bus) in get(base_network, "bus", Dict())
        if !haskey(settings["bus"], id)
            settings["bus"][id] = Dict{String,Any}()
        end

        settings["bus"][id][bound_name] = fill(bound_value * bus_vbase[id], length(bus["terminals"]))
    end
end


"helper function that applies settings to the network objects of `type`"
function _apply_to_network!(network::Dict{String,<:Any}, type::String, data::Dict{String,<:Any})
    for (_,nw) in network["nw"]
        if haskey(nw, type)
            for (id, _data) in data
                if haskey(nw[type], id)
                    merge!(nw[type][id], _data)
                end
            end
        end
    end
end
