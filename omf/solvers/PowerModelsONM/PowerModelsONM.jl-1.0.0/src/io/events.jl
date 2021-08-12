"""
    parse_events!(args::Dict{String,<:Any}; validate::Bool=true, apply::Bool=true)::Dict{String,Any}

Parses events file in-place using [`parse_events`](@ref parse_events), for use inside of [`entrypoint`](@ref entrypoint).

If `apply`, will apply the events to the multinetwork data structure.

## Validation

If `validate=true` (default), the parsed data structure will be validated against the latest [Events Schema](@ref Events-Schema).
"""
function parse_events!(args::Dict{String,<:Any}; validate::Bool=true, apply::Bool=true)::Dict{String,Any}
    if !isempty(get(args, "events", ""))
        if isa(args["events"], String)
            if isa(get(args, "network", ""), Dict)
                args["raw_events"] = parse_events(args["events"]; validate=validate)
                args["events"] = parse_events(deepcopy(args["raw_events"]), args["network"])
            else
                @warn "no network is loaded, cannot convert events into native multinetwork structure"
                args["events"] = parse_events(args["events"])
            end
        elseif isa(args["events"], Vector) && isa(get(args, "network", ""), Dict)
            parse_events(args["events"], args["network"])
        end
    else
    end

    if apply
        if isa(get(args, "network", ""), Dict)
            apply_events!(args)
        else
            error("cannot apply events, no multinetwork is loaded in 'network'")
        end
    end

    return args["events"]
end


"""
    parse_events(events_file::String; validate::Bool=true)::Vector{Dict{String,Any}}

Parses an events file into a raw events data structure

## Validation

If `validate=true` (default), the parsed data structure will be validated against the latest [Events Schema](@ref Events-Schema).
"""
function parse_events(events_file::String; validate::Bool=true)::Vector{Dict{String,Any}}
    events = Vector{Dict{String,Any}}(JSON.parsefile(events_file))

    if validate && !validate_events(events)
        error("'events' file could not be validated")
    end

    return events
end


"helper function to convert JSON data types to native data types (Enums) in events"
function _convert_event_data_types!(events::Vector{<:Dict{String,<:Any}})::Vector{Dict{String,Any}}
    for event in events
        for (k,v) in event["event_data"]
            if k == "dispatchable"
                event["event_data"][k] = PMD.Dispatchable(Int(v))
            end

            if k == "state"
                event["event_data"][k] = Dict("open" => PMD.OPEN, "closed" => PMD.CLOSED)[lowercase(string(v))]
            end

            if k == "status"
                event["event_data"][k] = PMD.Status(Int(v))
            end
        end
    end

    return events
end


"""
    parse_events(raw_events::Vector{<:Dict{String,<:Any}}, mn_data::Dict{String,<:Any})::Dict{String,Any}

Converts `raw_events`, e.g. loaded from JSON, and therefore in the format Vector{Dict}, to an internal data structure
that closely matches the multinetwork data structure for easy merging (applying) to the multinetwork data structure.

Will attempt to find the correct subnetwork from the specified timestep by using "mn_lookup" in the multinetwork
data structure.

## Switch events

Will find the correct switch id from a `source_id`, i.e., the asset_type.name from the source file, which for switches
will be `line.name`, and create a data structure containing the properties defined in `event_data` under the native
ENGINEERING switch id.

## Fault events

Will attempt to find the appropriate switches that need to be OPEN to isolate a fault, and disable them, i.e.,
set `dispatchable=false`, until the end of the `duration` of the fault, which is specified in milliseconds.

It will re-enable the switches, i.e., set `dispatchable=true` after the fault has ended, if the next timestep
exists, but will not automatically set the switches to CLOSED again; this is a decision for the algorithm
[`optimize_switches`](@ref optimize_switches) to make.
"""
function parse_events(raw_events::Vector{<:Dict{String,<:Any}}, mn_data::Dict{String,<:Any})::Dict{String,Any}
    _convert_event_data_types!(raw_events)

    events = Dict{String,Any}()
    for event in raw_events
        n = _find_nw_id_from_timestep(mn_data, event["timestep"])

        if !haskey(events, n)
            events[n] = Dict{String,Any}(
                "switch" => Dict{String,Any}()
            )
        end

        if event["event_type"] == "switch"
            switch_id = _find_switch_id_from_source_id(mn_data["nw"][n], event["affected_asset"])

            events[n]["switch"][switch_id] = Dict{String,Any}(
                k => v for (k,v) in event["event_data"]
            )
        elseif event["event_type"] == "fault"
            switch_ids = _find_switch_ids_by_faulted_asset(mn_data["nw"][n], event["affected_asset"])
            n_next = _find_next_nw_id_from_fault_duration(mn_data, n, event["event_data"]["duration"])

            if !ismissing(n_next)
                if !haskey(events, n_next)
                    events[n_next] = Dict{String,Any}(
                        "switch" => Dict{String,Any}()
                    )
                end
            end

            for switch_id in switch_ids
                events[n]["switch"][switch_id] = Dict{String,Any}(
                    "state" => PMD.OPEN,
                    "dispatchable" => PMD.NO,
                )
                if !ismissing(n_next) && !haskey(events[n_next], switch_id)  # don't do it if there is already an event defined for switch_id at next timestep
                    events[n_next]["switch"][switch_id] = Dict{String,Any}(
                        "dispatchable" => PMD.YES,
                    )
                end
            end
        else
            @warn "event_type '$(event["event_type"])' not recognized, skipping"
        end
    end

    return events
end


"""
    parse_events(events_file::String, mn_data::Dict{String,<:Any}; validate::Bool=true)::Dict{String,Any}

Parses raw events from `events_file` and passes it to [`parse_events`](@ref parse_events) to convert to the
native data type.

## Validation

If `validate=true` (default), the parsed data structure will be validated against the latest [Events Schema](@ref Events-Schema).
"""
function parse_events(events_file::String, mn_data::Dict{String,<:Any}; validate::Bool=true)::Dict{String,Any}
    raw_events = parse_events(events_file; validate=validate)
    events = parse_events(raw_events, mn_data)
end


"""
    apply_events!(args::Dict{String,<:Any})::Dict{String,Any}

Applies events in-place using [`apply_events`](@ref apply_events), for use inside of [`entrypoint`](@ref entrypoint)
"""
function apply_events!(args::Dict{String,<:Any})::Dict{String,Any}
    args["network"] = apply_events(args["network"], args["events"])
end


"""
    apply_events(network::Dict{String,<:Any}, events::Dict{String,<:Any})::Dict{String,Any}

Creates a copy of the multinetwork data structure `network` and applies the events in `events`
to that data.
"""
function apply_events(network::Dict{String,<:Any}, events::Dict{String,<:Any})::Dict{String,Any}
    mn_data = deepcopy(network)

    ns = sort([parse(Int, i) for i in keys(network["nw"])])
    for (i,n) in enumerate(ns)
        nw = get(events, "$n", Dict())
        for (t,objs) in nw
            for (id,obj) in objs
                # Apply to all subnetworks starting with the current one until the end
                for j in ns[i:end]
                    merge!(mn_data["nw"]["$j"][t][id], obj)
                end
            end
        end
    end

    return mn_data
end


"helper function to find a switch id in the network model based on the dss `source_id`"
function _find_switch_id_from_source_id(network::Dict{String,<:Any}, source_id::String)::String
    for (id, switch) in get(network, "switch", Dict())
        if switch["source_id"] == source_id
            return id
        end
    end
    error("switch '$(source_id)' not found in network model, aborting")
end


"helper function to find which switches need to be opened to isolate a fault on asset given by `source_id`"
function _find_switch_ids_by_faulted_asset(network::Dict{String,<:Any}, source_id::String)::Vector{String}
    # TODO algorithm for isolating faults (heuristic)
end


"helper function to find the multinetwork id of the subnetwork corresponding most closely to a `timestep`"
function _find_nw_id_from_timestep(network::Dict{String,<:Any}, timestep::Union{Real,String})::String
    @assert PMD.ismultinetwork(network) "network data structure is not multinetwork"

    if isa(timestep, Int) && all(isa(v, Int) for v in values(network["mn_lookup"])) || isa(timestep, String)
        if isa(timestep, String)
            timestep = all(isa(v, Int) for v in values(network["mn_lookup"])) ? parse(Int, timestep) : all(isa(v, Real) for v in values(network["mn_lookup"])) ? parse(Float16, timestep) : timestep
        end

        for (nw_id,ts) in network["mn_lookup"]
            if ts == timestep
                return nw_id
            end
        end
    else
        for (nw_id,ts) in network["mn_lookup"]
            if ts ≈ timestep
                return nw_id
            end
        end

        timesteps = sort(collect(values(network["mn_lookup"])))
        dist = timesteps .- timestep
        ts = findfirst(x->x≈minimum(dist[dist .> 0]), timesteps)
        for (nw_id, ts) in network["mn_lookup"]
            if ts == timestep
                return nw_id
            end
        end
    end
    error("could not find timestep '$(timestep)' in the multinetwork data structure")
end


"helper function to find the next timestep following a fault given its duration in ms"
function _find_next_nw_id_from_fault_duration(network::Dict{String,<:Any}, nw_id::String, duration::Real)::Union{String,Missing}
    current_timestep = network["mn_lookup"][nw_id]
    mn_lookup_reverse = Dict{Any,String}(v => k for (k,v) in network["mn_lookup"])

    timesteps = sort(collect(values(network["mn_lookup"])))
    dist = timesteps .- current_timestep + (duration / 3.6e6)  # duration is in ms, timestep in hours
    if all(dist .< 0)
        return missing
    else
        ts = findfirst(x->x ≈ minimum(dist[dist .> 0]), timesteps)
        return mn_lookup_reverse[ts]
    end
end
