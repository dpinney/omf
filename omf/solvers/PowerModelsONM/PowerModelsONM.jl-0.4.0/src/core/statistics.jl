import Statistics: mean


function get_voltage_stats(sol_pu::Dict{Any,<:Any}, data_eng::Dict{String,<:Any})
    voltages = [get(bus, "vm", zeros(length(data_eng["bus"][id]["terminals"]))) for (id,bus) in sol_pu["bus"]]

    return minimum(minimum.(voltages)), mean(mean.(voltages)), maximum(maximum.(voltages))
end


function get_timestep_voltage_stats!(output::Dict{String,<:Any}, sol_pu::Dict{String,<:Any}, data_eng::Dict{String,<:Any})
    for i in sort([parse(Int, k) for k in keys(sol_pu["nw"])])
        min_v, mean_v, max_v = get_voltage_stats(sol_pu["nw"]["$i"], data_eng)
        push!(output["Voltages"]["Min voltage (p.u.)"], min_v)
        push!(output["Voltages"]["Mean voltage (p.u.)"], mean_v)
        push!(output["Voltages"]["Max voltage (p.u.)"], max_v)
    end
end


function get_timestep_load_served!(output::Dict{String,<:Any}, sol_si::Dict{String,<:Any}, mn_data_eng::Dict{String,<:Any})
    for i in sort([parse(Int, k) for k in keys(sol_si["nw"])])
        original_load = sum([sum(load["pd_nom"]) for (_,load) in mn_data_eng["nw"]["$i"]["load"]])
        feeder_served_load = sum([sum(vs["pg"]) for (_,vs) in sol_si["nw"]["$i"]["voltage_source"]])
        der_non_storage_served_load = !isempty(get(sol_si["nw"]["$i"], "generator", Dict())) || !isempty(get(sol_si["nw"]["$i"], "solar", Dict())) ? sum([sum(g["pg"]) for type in ["solar", "generator"] for (_,g) in get(sol_si["nw"]["$i"], type, Dict())]) : 0.0
        der_storage_served_load = !isempty(get(sol_si["nw"]["$i"], "storage", Dict())) ? sum([-sum(s["ps"]) for (_,s) in get(sol_si["nw"]["$i"], "storage", Dict())]) : 0.0
        microgrid_served_load = (der_non_storage_served_load + der_storage_served_load) / original_load * 100
        _bonus_load = (microgrid_served_load - 100)

        push!(output["Load served"]["Feeder load (%)"], feeder_served_load / original_load * 100)  # CHECK
        push!(output["Load served"]["Microgrid load (%)"], microgrid_served_load)  # CHECK
        push!(output["Load served"]["Bonus load via microgrid (%)"], _bonus_load > 0 ? _bonus_load : 0.0)  # CHECK
    end
end


function get_timestep_generator_profiles!(output::Dict{String,<:Any}, sol_si::Dict{String,<:Any})
    for i in sort([parse(Int, k) for k in keys(sol_si["nw"])])
        push!(output["Generator profiles"]["Grid mix (kW)"], sum(Float64[sum(vsource["pg"]) for (_,vsource) in get(sol_si["nw"]["$i"], "voltage_source", Dict())]))
        push!(output["Generator profiles"]["Solar DG (kW)"], sum(Float64[sum(solar["pg"]) for (_,solar) in get(sol_si["nw"]["$i"], "solar", Dict())]))
        push!(output["Generator profiles"]["Energy storage (kW)"], sum(Float64[-sum(storage["ps"]) for (_,storage) in get(sol_si["nw"]["$i"], "storage", Dict())]))
        push!(output["Generator profiles"]["Diesel DG (kW)"], sum(Float64[sum(gen["pg"]) for (_,gen) in get(sol_si["nw"]["$i"], "generator", Dict())]))
    end
end


function get_timestep_powerflow_output!(output::Dict{String,<:Any}, sol_pu::Dict{String,<:Any}, data_eng::Dict{String,<:Any})
    for i in sort([parse(Int, k) for k in keys(sol_pu["nw"])])
        n = "$i"
        nw = sol_pu["nw"][n]
        nw_pf = Dict{String,Any}(
            "bus" => Dict{String,Any}()
        )
        for (id,bus) in get(nw, "bus", Dict())
            nw_pf["bus"][id] = Dict{String,Any}("voltage (V)" => get(bus, "vm", zeros(length(data_eng["bus"][id]["terminals"]))))
        end

        if !isempty(get(nw, "storage", Dict()))
            nw_pf["storage"] = Dict{String,Any}()
            for (id,strg) in nw["storage"]
                nw_pf["storage"][id] = Dict{String,Any}(
                    "real power setpoint (kW)" => get(strg, "ps", zeros(length(data_eng["storage"][id]["connections"]))),
                    "reactive power setpoint (kVar)" => get(strg, "qs", zeros(length(data_eng["storage"][id]["connections"])))
                )
            end
        end

        for gen_type in ["solar", "generator", "voltage_source"]
            if !isempty(get(nw, gen_type, Dict()))
                nw_pf[gen_type] = Dict{String,Any}()
                for (id,gen) in nw[gen_type]
                    nw_pf[gen_type][id] = Dict{String,Any}(
                        "real power setpoint (kW)" => get(gen, "pg", zeros(length(data_eng[gen_type][id]["connections"]))),
                        "reactive power setpoint (kVar)" => get(gen, "qg", zeros(length(data_eng[gen_type][id]["connections"])))
                    )
                end
            end
        end

        push!(output["Powerflow output"], nw_pf)
    end
end


function get_timestep_device_actions!(output::Dict{String,<:Any}, osw_result::Vector{<:Dict{String,<:Any}}, mn_data_math::Dict{String,<:Any})
    switch_map = build_switch_map(mn_data_math["map"])
    load_map = build_device_map(mn_data_math["map"], "load")
    for i in sort([parse(Int, k) for k in keys(mn_data_math["nw"])])
        n = "$i"
        nw = mn_data_math["nw"][n]
        oswr = get(osw_result[i], "solution", Dict())

        _out = Dict{String,Any}(
            "Switch configurations" => Dict{String,Any}(switch_map[l] => isa(switch["state"], PMD.SwitchState) ? lowercase(string(switch["state"])) : lowercase(string(PMD.SwitchState(Int(round(switch["state"]))))) for (l, switch) in get(mn_data_math["nw"]["$i"], "switch", Dict()))
        )

        shedded_loads = Vector{String}([])
        for (id, load) in get(oswr, "load", Dict())
            if round(get(load, "status", 1)) ≉ 1
               push!(shedded_loads, load_map[id])
            end
        end

        _out["Shedded loads"] = shedded_loads

        push!(output["Device action timeline"], _out)
    end
end


function get_timestep_storage_soc!(output::Dict{String,<:Any}, sol_si::Dict{String,<:Any}, data_eng::Dict{String,<:Any})
    for i in sort([parse(Int, k) for k in keys(sol_si["nw"])])
        push!(output["Storage SOC (%)"], 100.0 * sum(strg["se"] for strg in values(sol_si["nw"]["$i"]["storage"])) / sum(strg["energy_ub"] for strg in values(data_eng["storage"])))
    end
end


function get_timestep_protection_settings!(output_data::Dict{String,<:Any}, protection_data::Dict)
    if !isempty(protection_data)
        prop_names = propertynames(first(protection_data).first)
        for device_settings in output_data["Device action timeline"]
            if haskey(device_settings, "Switch configurations")
                _config_dict = device_settings["Switch configurations"]
                sw_config = NamedTuple{prop_names}(Tuple(get(_config_dict, string(name), "open") for name in prop_names))
                push!(output_data["Protection Settings"], haskey(protection_data, sw_config) ? protection_data[sw_config] : Dict{String,Any}())
            end
        end
    end
end


""
function get_timestep_fault_currents!(output_data::Dict{String,<:Any}, fault_results::Vector{<:Dict{String,<:Any}})
    for fault_result in fault_results
        _output = Dict{String,Any}()
        for (bus_id, bus_faults) in fault_result
            for (fault_type, fault_type_results) in bus_faults
                if !haskey(_output, fault_type)
                    _output[fault_type] = Dict{String,Any}()
                end
                _output[fault_type][bus_id] = get(get(get(get(get(fault_type_results, "1", Dict()), "solution", Dict()), "fault", Dict()), "bus", Dict()), "current", [])
            end
        end
        push!(output_data["Fault currents"], _output)
    end
end


""
function get_timestep_stability!(output_data::Dict{String,<:Any}, is_stable::Vector{<:Bool})
    output_data["Small signal stable"] = is_stable
end


""
function get_switch_changes!(output_data::Dict{String,<:Any}, mn_data_eng::Dict{String,<:Any})
    output_data["Switch changes"] = Vector{Vector{String}}([])
    _switch_configs = Dict(s => Dict(PMD.OPEN => "open", PMD.CLOSED => "closed")[sw["state"]] for (s,sw) in mn_data_eng["nw"]["1"]["switch"])
    for timestep in output_data["Device action timeline"]
        switch_configs = timestep["Switch configurations"]
        _changes = Vector{String}([])
        for (switch, state) in switch_configs
            if get(_switch_configs, switch, state) != state
                push!(_changes, switch)
            end
        end
        _switch_configs = deepcopy(switch_configs)
        push!(output_data["Switch changes"], _changes)
    end
end
