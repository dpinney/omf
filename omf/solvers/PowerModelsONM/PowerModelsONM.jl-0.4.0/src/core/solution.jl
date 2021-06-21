""
function transform_solutions(sol_math::Dict{String,<:Any}, data_math::Dict{String,<:Any})::Tuple{Dict{String,Any},Dict{String,Any}}
    sol_pu = PMD.transform_solution(sol_math, data_math; make_si=false)
sol_si = PMD.transform_solution(sol_math, data_math; make_si=true)

    return sol_pu, sol_si
end


""
function apply_load_shed!(mn_data_math::Dict{String,<:Any}, result::Dict{String,<:Any})
    for (n,nw) in result["solution"]["nw"]
        for (l, load) in get(nw, "load", Dict())
            mn_data_math["nw"][n]["load"][l]["status"] = load["status"]
        end
    end
end


""
function sol_ldf2acr!(pm::PMD.LPUBFDiagModel, solution::Dict{String,<:Any})
    if haskey(solution, "nw")
        nws_data = solution["nw"]
        nws_pm_data = pm.data["nw"]
    else
        nws_data = Dict("0" => solution)
        nws_pm_data = Dict("0" => pm.data)
    end

    for (n, nw_data) in nws_data
        if haskey(nw_data, "bus")
            for (i, bus) in nw_data["bus"]
                if haskey(bus, "w")
                    bus_data = nws_pm_data[n]["bus"][i]
                    bus["vr"] = sqrt.(bus["w"]) .* [cos.(PMD._wrap_to_pi(zeros(3)))[t] for t in bus_data["terminals"][.!bus_data["grounded"]]]
                    bus["vi"] = sqrt.(bus["w"]) .* [sin.(PMD._wrap_to_pi(zeros(3)))[t] for t in bus_data["terminals"][.!bus_data["grounded"]]]
                end
            end
        end
    end
end


""
function sol_ldf2acp!(pm::PMD.LPUBFDiagModel, solution::Dict{String,<:Any})
    if haskey(solution, "nw")
        nws_data = solution["nw"]
        nws_pm_data = pm.data["nw"]
    else
        nws_data = Dict("0" => solution)
        nws_pm_data = Dict("0" => pm.data)
    end

    for (n, nw_data) in nws_data
        if haskey(nw_data, "bus")
            for (i, bus) in nw_data["bus"]
                if haskey(bus, "w")
                    bus_data = nws_pm_data[n]["bus"][i]
                    bus["vm"] = sqrt.(bus["w"])
                    bus["va"] = [sin.(PMD._wrap_to_pi(zeros(3)))[t] for t in bus_data["terminals"][.!bus_data["grounded"]]]
                end
            end
        end
    end
end


"nothing to do"
function sol_ldf2lindistflow!(pm::PMD.LPUBFDiagModel, solution::Dict{String,<:Any})
end


"nothing to do"
function sol_ldf2nfa!(pm::PMD.LPUBFDiagModel, solution::Dict{String,<:Any})
end


""
function update_start_values!(data::Dict{String,<:Any}, solution::Dict{String,<:Any})
    if haskey(solution, "nw")
        nws_solution = solution["nw"]
        nws_data = data["nw"]
    else
        nws_solution = Dict("0" => solution)
        nws_data = Dict("0" => data)
    end

    for (n, nw_sol) in nws_solution
        for (type, objs) in nw_sol
            if isa(objs, Dict)
                for (i, obj) in objs
                    for (k, v) in obj
                        if !endswith(k, "_start")
                            nws_data[n][type][i]["$(k)_start"] = v
                        end
                    end
                end
            end
        end
    end
end


""
function update_switch_settings!(data::Dict{String,<:Any}, solution::Dict{String,<:Any})
    if haskey(solution, "nw")
        nws_solution = solution["nw"]
        nws_data = data["nw"]
    else
        nws_solution = Dict("0" => solution)
        nws_data = Dict("0" => data)
    end

    for (n, nw_sol) in nws_solution
        for (l, switch) in get(nw_sol, "switch", Dict())
            if haskey(switch, "state")
                nws_data[n]["switch"][l]["state"] = switch["state"]
            end
        end
    end
end


""
function update_post_event_actions_load_shed!(events::Vector{<:Dict{String,<:Any}}, solution::Dict{String,<:Any}, map::Vector{<:Dict{String,<:Any}})
    load_map = build_device_map(map, "load")

    current_loadstatus = Dict(l => 1 for (_,l) in load_map)

    for (n, nw) in solution["nw"]
        timestep = parse(Int, n)

        for event in events
            event_timestep = Int(round(parse(Float64, event["timestep"])))

            if event_timestep == timestep
                for (l, load) in get(solution, "load", Dict())
                    if load["status"] != current_loadstatus[load_map[l]]
                        if !haskey(event["event_data"], "post_event_actions")
                            event["event_data"]["post_event_actions"] = []
                        end
                        push!(event["event_data"]["post_event_actions"], Dict{String,Any}(
                            "timestep" => "$timestep",
                            "event_type" => "loadshed",
                            "affected_asset" => "load.$(load_map[l])",
                            "event_data" => Dict{String,Any}(
                                "status" => 0
                            )
                        ))
                        current_loadstatus[load_map[l]] = load["status"]
                    end
                end
            end
        end
    end
end


""
function update_storage_capacity!(data::Dict{String,<:Any}, solution::Dict{String,<:Any})
    for (i, strg) in get(solution, "storage", Dict())
        # data["storage"][i]["energy"] = data["time_elapsed"]*(data["storage"][i]["charge_efficiency"]*strg["sc"] - strg["sd"]/data["storage"][i]["discharge_efficiency"]) + strg["energy"]
        data["storage"][i]["_energy"] = deepcopy(data["storage"][i]["energy"])
        data["storage"][i]["energy"] = strg["se"]
    end
end
