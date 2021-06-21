const pmd_component_status = Dict(
    "bus" => "bus_type",
    "load" => "status",
    "shunt" => "status",
    "gen" => "gen_status",
    "storage" => "status",
    "switch" => "status",
    "branch" => "br_status",
    "transformer" => "status",
)

const pmd_component_status_inactive = Dict(
    "bus" => 4,
    "load" => 0,
    "shunt" => 0,
    "gen" => 0,
    "storage" => 0,
    "switch" => 0,
    "branch" => 0,
    "transformer" => 0,
)


""
function _make_dict_keys_str(dict::Dict{<:Any,<:Any})
    o = Dict{String,Any}()
    for (k, v) in dict
        if isa(v, Dict)
            v = _make_dict_keys_str(v)
        end
        o[string(k)] = v
    end

    return o
end


""
function make_multinetwork!(data_eng, data_math, sol_pu, sol_si)
    if !haskey(data_eng, "time_series")
        data_eng["time_series"] = Dict{String,Any}("0" => Dict{String,Any}("time" => [0.0]))
    end

    if !haskey(data_math, "nw")
        sol_pu = Dict{String,Any}("nw" => Dict{String,Any}("0" => sol_pu))
        sol_si = Dict{String,Any}("nw" => Dict{String,Any}("0" => sol_si))
    end
end


""
function get_timestep(timestep::Union{Int,String}, network::Dict{String,<:Any})
    if isa(timestep, Int)
        return timestep
    else
        # TODO: Support timesteps in eng multinetwork data structure (PMD)
        Int(round(parse(Float64, timestep)))
    end
end


"expects engineering network (multi of single)"
function apply_events!(network::Dict{String,Any}, events::Vector{<:Dict{String,Any}})
    for event in events
        source_id = event["affected_asset"]
        asset_type, asset_name = split(lowercase(source_id), ".")
        timestep = event["timestep"]

        if event["event_type"] == "switch"
            start_timestep = get_timestep(timestep, network)
            if haskey(network, "nw")
                if any(haskey(nw["switch"], asset_name) for (_,nw) in network["nw"])
                    for (n, nw) in network["nw"]
                        if parse(Int, n) >= start_timestep
                            if haskey(nw["switch"], asset_name)
                                if haskey(event["event_data"], "status")
                                    nw["switch"][asset_name]["status"] = PMD.Status(event["event_data"]["status"])
                                end

                                if haskey(event["event_data"], "state")
                                    nw["switch"][asset_name]["state"] = Dict{String,PMD.SwitchState}("closed"=>PMD.CLOSED, "open"=>PMD.OPEN)[lowercase(event["event_data"]["state"])]
                                end

                                if haskey(event["event_data"], "dispatchable")
                                    nw["switch"][asset_name]["dispatchable"] = event["event_data"]["dispatchable"] ? PMD.YES : PMD.NO
                                end
                            else
                                @info "switch '$(asset_name)' mentioned in events does not exist in data set at timestep $(n)"
                            end
                        end
                    end
                else
                    @info  "switch '$(asset_name)' mentioned in events does not exist in data set"
                end
            else
                network["switch"][asset_name]["state"] = Dict{String,PMD.SwitchState}("closed"=>PMD.CLOSED, "open"=>PMD.OPEN)
            end

        else
            @warn "event of type '$(event["event_type"])' at timestep $(timestep) is not yet supported in PowerModelsONM"
        end
    end
end


""
function build_device_map(map::Vector{<:Dict{String,<:Any}}, device_type::String)::Dict{String,String}
    Dict{String,String}(
        string(split(item["to"], ".")[end]) => item["from"] for item in map if endswith(item["unmap_function"], "$(device_type)!")
    )
end


""
function build_switch_map(map::Vector)::Dict{String,String}
    switch_map = Dict{String,String}()
    for item in map
        if endswith(item["unmap_function"], "switch!")
            if isa(item["to"], Array)
                for _to in item["to"]
                    if startswith(_to, "switch")
                        math_id = split(_to, ".")[end]
                    end
                end
            else
                math_id = split(item["to"], ".")[end]
            end
            switch_map[math_id] = item["from"]
        end
    end
    return switch_map
end


""
function propagate_switch_settings!(mn_data_eng::Dict{String,<:Any}, mn_data_math::Dict{String,<:Any})
    switch_map = build_switch_map(mn_data_math["map"])

    for (n, nw) in mn_data_math["nw"]
        for (i,sw) in get(nw, "switch", Dict())
            mn_data_eng["nw"][n]["switch"][switch_map[i]]["state"] = PMD.SwitchState(Int(round(sw["state"])))
        end

        blocks = identify_load_blocks(nw)
        warm_blocks = are_blocks_warm(nw, blocks)
        for (block, is_warm) in warm_blocks
            if is_warm != 1
                for bus in block
                    nw["bus"]["$bus"]["bus_type"] = 4
                end
            end
        end

        PMD._PM.propagate_topology_status!(nw)
    end
end


# TODO: Remove once storage supported in IVR, assumes MATH Model, with solution already
"converts storage to generators"
function convert_storage!(nw::Dict{String,<:Any})
    for (i, strg) in get(nw, "storage", Dict())
        nw["gen"]["$(length(nw["gen"])+1)"] = Dict{String,Any}(
            "name" => strg["name"],
            "gen_bus" => strg["storage_bus"],
            "connections" => strg["connections"],
            "configuration" => PMD.WYE,
            "control_mode" => PMD.FREQUENCYDROOP,
            "gen_status" => strg["status"],

            "pmin" => strg["ps"] .- 1e-9,
            "pmax" => strg["ps"] .+ 1e-9,
            "pg" => strg["ps"],
            "qmin" => strg["qs"] .- 1e-9,
            "qmax" => strg["qs"] .+ 1e-9,
            "qg" => strg["qs"],

            "model" => 2,
            "startup" => 0,
            "shutdown" => 0,
            "cost" => [100.0, 0.0],
            "ncost" => 2,

            "index" => length(nw["gen"])+1,
            "source_id" => strg["source_id"],

            "vbase" => nw["bus"]["$(strg["storage_bus"])"]["vbase"],  # grab vbase from bus
            "zx" => [0, 0, 0], # dynamics required by PMP, treat like voltage source
        )
    end
end


"voltage angle bounds"
function apply_voltage_angle_bounds!(eng::Dict{String,<:Any}, vad::Real)
    if haskey(eng, "line")
        for (_,line) in eng["line"]
            line["vad_lb"] = fill(-vad, length(line["f_connections"]))
            line["vad_ub"] = fill( vad, length(line["f_connections"]))
        end
    end
end


function identify_cold_loads(data)
    blocks = identify_load_blocks(data)
    is_warm = are_blocks_warm(data, blocks)

    load2block_map = Dict()
    for (l,load) in get(data, "load", Dict())
        for block in blocks
            if load["load_bus"] in block
                load2block_map[parse(Int,l)] = block
                break
            end
        end
    end

    return Dict(l => !is_warm[block] for (l,block) in load2block_map)
end


function identify_load_blocks(data; edges=["branch", "transformer", "switch"])
    active_bus = Dict{Any,Dict{String,Any}}(x for x in data["bus"] if x.second[pmd_component_status["bus"]] != pmd_component_status_inactive["bus"])
    active_bus_ids = Set{Any}([parse(Int,i) for (i,bus) in active_bus])

    neighbors = Dict{Any,Vector{Any}}(i => [] for i in active_bus_ids)
    for edge_type in edges
        for (id, edge_obj) in get(data, edge_type, Dict{Any,Dict{String,Any}}())
            if edge_type == "switch"
                if edge_obj[pmd_component_status[edge_type]] != pmd_component_status_inactive[edge_type] && edge_obj["state"] != 0
                    push!(neighbors[edge_obj["f_bus"]], edge_obj["t_bus"])
                    push!(neighbors[edge_obj["t_bus"]], edge_obj["f_bus"])
                end
            else
                if edge_obj[pmd_component_status[edge_type]] != pmd_component_status_inactive[edge_type]
                    push!(neighbors[edge_obj["f_bus"]], edge_obj["t_bus"])
                    push!(neighbors[edge_obj["t_bus"]], edge_obj["f_bus"])
                end
            end
        end
    end

    component_lookup = Dict(i => Set{Any}([i]) for i in active_bus_ids)
    touched = Set{Any}()

    for i in active_bus_ids
        if !(i in touched)
            PMD._PM._cc_dfs(i, neighbors, component_lookup, touched)
        end
    end

    ccs = (Set(values(component_lookup)))

    return ccs
end


function are_blocks_warm(data, blocks)
    active_gen_buses = Set([gen["gen_bus"] for (_,gen) in get(data, "gen", Dict()) if gen[pmd_component_status["gen"]] != pmd_component_status_inactive["gen"]])
    active_storage_buses = Set([strg["storage_bus"] for (_,strg) in get(data, "storage", Dict()) if strg[pmd_component_status["storage"]] != pmd_component_status_inactive["storage"]])

    is_warm = Dict(block => false for block in blocks)
    for block in blocks
        for bus in block
            if bus in active_gen_buses || bus in active_storage_buses
                is_warm[block] = true
                break
            end
        end
    end
    return is_warm
end


function is_block_warm(data, block)
    active_gen_buses = Set([gen["gen_bus"] for (_,gen) in get(data, "gen", Dict()) if gen[pmd_component_status["gen"]] != pmd_component_status_inactive["gen"]])
    active_storage_buses = Set([strg["storage_bus"] for (_,strg) in get(data, "storage", Dict()) if strg[pmd_component_status["storage"]] != pmd_component_status_inactive["storage"]])

    for bus in block
        if bus in active_gen_buses || bus in active_storage_buses
            return true
            break
        end
    end
    return false
end


""
function adjust_line_limits!(data_eng::Dict{String,<:Any}; scale::Real=10.0)
    for type in ["line", "switch"]
        if haskey(data_eng, type)
            for (l, line) in data_eng[type]
                for k in ["cm_ub", "cm_ub_b", "cm_ub_c"]
                    if haskey(line, k)
                        line[k] .*= scale
                    end
                end
            end
        end
    end
end
